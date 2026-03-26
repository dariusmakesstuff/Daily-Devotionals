#!/usr/bin/env python3
"""Patch DV001: multi-provider TTS Code nodes + Media/ loop catalog."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "n8n" / "workflows" / "DV001_Daily_Devotional_Orchestrator.json"
CODES = ROOT / "n8n" / "code" / "generated_tts_codes.json"

SELECT_BG_JS = r"""// Select Episode Assets — background loop + voice pair (same posture → ElevenLabs IDs; TTS provider is separate)
// Stock loops: gs://<gcs_bucket>/<gcs_media_folder>/filename.mp4 (default folder Media)

const config = $('Set Global Config').first().json;
const worldPulse = $('🌐 Merge Signal Source').first().json.world_pulse;
const toneAudienceFraming = (() => {
  try { return $('🎨 Audience Framing Agent').first().json.output; } catch (e) { return {}; }
})();

const posture = toneAudienceFraming?.emotional_posture || 'anchor';
const hookEnergy = toneAudienceFraming?.hook_energy || posture;
const toneLean = worldPulse?.tone_lean || 'WARM_HOPEFUL';

const ar = String(config.aspect_ratio || '9:16').trim();
const portraitTarget = ar === '9:16' || ar.toLowerCase().includes('9:16') || ar.toLowerCase().includes('portrait');

const PORTRAIT_LOOPS = [
  '12750962_2160_3840_60fps.mp4',
  '13999442_1080_1920_25fps.mp4',
  '14259282-uhd_2160_3840_60fps.mp4',
  '14345562_1080_1920_60fps.mp4',
  '14501575_2160_3840_30fps.mp4',
  '14710258_2160_3840_30fps.mp4',
  '17416254-hd_1080_1920_30fps.mp4',
  '5199835-uhd_2160_3840_25fps.mp4',
  '5206099-uhd_2160_3840_25fps.mp4',
  '6616737-uhd_2160_4096_25fps.mp4',
  '7220081-uhd_2160_3840_25fps.mp4',
  '7326751-hd_1080_1920_24fps.mp4',
  '8483600-hd_1080_1920_25fps.mp4',
];

const LANDSCAPE_LOOPS = [
  '13967916_3840_2160_30fps.mp4',
  '14572343_3840_2160_30fps.mp4',
  '14904571_1920_1080_60fps.mp4',
  '20508990-hd_1920_1080_25fps.mp4',
  '854101-hd_1920_1080_25fps.mp4',
];

const toneMap = {
  WARM_HOPEFUL: 'anchor',
  LIGHT_JOYFUL: 'fire',
  HEAVY_REFLECTIVE: 'shepherd',
  WONDER: 'anchor',
  FUNNY_REAL: 'fire',
};

const resolvedPosture = posture || toneMap[toneLean] || 'anchor';
const pool = portraitTarget ? PORTRAIT_LOOPS : LANDSCAPE_LOOPS;
const postureOffset = { anchor: 0, fire: 2, shepherd: 5, challenger: 8 };
const off = postureOffset[resolvedPosture] !== undefined ? postureOffset[resolvedPosture] : 0;
const today = new Date().toISOString().split('T')[0];
const dayNum = parseInt(today.replace(/-/g, ''), 10);
const idx = (off + dayNum) % pool.length;
const filename = pool[idx];

let mediaFolder = String(config.gcs_media_folder || 'Media').trim();
mediaFolder = mediaFolder.replace(/^\/+/, '').replace(/\/+$/, '') || 'Media';
const bucket = config.gcs_bucket;
const loopUrl = `https://storage.googleapis.com/${bucket}/${mediaFolder}/${filename}`;
const bgGcs = `gs://${bucket}/${mediaFolder}/${filename}`;

const voiceKey = (role, energy) => `voice_${role}_${energy}`;
const hostVoiceId = config[voiceKey('host', hookEnergy)] || config.elevenlabs_voice_id;
const reflVoiceId = config[voiceKey('reflection', hookEnergy)] || config.elevenlabs_reflection_voice_id;
const hostVoiceLand = config[voiceKey('host', resolvedPosture)] || config.elevenlabs_voice_id;
const reflVoiceLand = config[voiceKey('reflection', resolvedPosture)] || config.elevenlabs_reflection_voice_id;
const musicTrack = `ambient_${resolvedPosture}.mp3`;

return {
  json: {
    background_clip_id: filename,
    background_gcs_uri: bgGcs,
    loop_url: loopUrl,
    emotional_posture: resolvedPosture,
    hook_energy: hookEnergy,
    host_voice_id: hostVoiceId,
    reflection_voice_id: reflVoiceId,
    host_voice_id_landing: hostVoiceLand,
    reflection_voice_id_landing: reflVoiceLand,
    music_gcs_uri: `gs://${bucket}/music/${musicTrack}`,
    tts_provider: (config.tts_provider || 'elevenlabs').toLowerCase().trim(),
  },
};
"""

TTS_NODE_MAP = {
    "817c45c5-4db7-414a-b20a-b745e48fa1f3": "host_full",
    "ef399d17-b75e-41f4-965d-e85a4f5a1c67": "reflection_full",
    "707d8848-8aa1-421c-a4b2-658cf4a42332": "host_short",
    "f1cda96b-bc11-4d6e-97e3-f86bcd7aa2fd": "reflection_short",
}

NEW_ASSIGNMENTS = [
    {
        "id": "gc-tts-provider",
        "name": "tts_provider",
        "type": "string",
        "value": "={{ ($env.TTS_PROVIDER || 'elevenlabs').toLowerCase().trim() }}",
    },
    {
        "id": "gc-openai-key-tts",
        "name": "openai_api_key",
        "type": "string",
        "value": "={{ $env.OPENAI_API_KEY || '' }}",
    },
    {
        "id": "gc-openai-tts-model",
        "name": "openai_tts_model",
        "type": "string",
        "value": "={{ $env.OPENAI_TTS_MODEL || 'gpt-4o-mini-tts' }}",
    },
    {
        "id": "gc-openai-voice-host",
        "name": "openai_voice_host",
        "type": "string",
        "value": "={{ $env.OPENAI_VOICE_HOST || '' }}",
    },
    {
        "id": "gc-openai-voice-refl",
        "name": "openai_voice_reflection",
        "type": "string",
        "value": "={{ $env.OPENAI_VOICE_REFLECTION || '' }}",
    },
    {
        "id": "gc-azure-key",
        "name": "azure_speech_key",
        "type": "string",
        "value": "={{ $env.AZURE_SPEECH_KEY || '' }}",
    },
    {
        "id": "gc-azure-region",
        "name": "azure_speech_region",
        "type": "string",
        "value": "={{ $env.AZURE_SPEECH_REGION || 'eastus' }}",
    },
    {
        "id": "gc-azure-voice-host",
        "name": "azure_voice_host",
        "type": "string",
        "value": "={{ $env.AZURE_VOICE_HOST || '' }}",
    },
    {
        "id": "gc-azure-voice-refl",
        "name": "azure_voice_reflection",
        "type": "string",
        "value": "={{ $env.AZURE_VOICE_REFLECTION || '' }}",
    },
    {
        "id": "gc-google-tts-key",
        "name": "google_tts_api_key",
        "type": "string",
        "value": "={{ $env.GOOGLE_TTS_API_KEY || '' }}",
    },
    {
        "id": "gc-google-voice-host-json",
        "name": "google_voice_host_json",
        "type": "string",
        "value": "={{ $env.GOOGLE_VOICE_HOST_JSON || '' }}",
    },
    {
        "id": "gc-google-voice-refl-json",
        "name": "google_voice_reflection_json",
        "type": "string",
        "value": "={{ $env.GOOGLE_VOICE_REFLECTION_JSON || '' }}",
    },
    {
        "id": "gc-gcs-media-folder",
        "name": "gcs_media_folder",
        "type": "string",
        "value": "={{ $env.GCS_MEDIA_FOLDER || 'Media' }}",
    },
]


def main() -> None:
    data = json.loads(WF.read_text(encoding="utf-8"))
    codes = json.loads(CODES.read_text(encoding="utf-8"))

    for node in data["nodes"]:
        nid = node.get("id")
        if nid in TTS_NODE_MAP:
            key = TTS_NODE_MAP[nid]
            node["type"] = "n8n-nodes-base.code"
            node["typeVersion"] = 2
            node["parameters"] = {"jsCode": codes[key]}
        if node.get("name") == "🌅 Select Background Loop":
            node["parameters"]["jsCode"] = SELECT_BG_JS
        if node.get("name") == "Set Global Config":
            assigns = node["parameters"]["assignments"]["assignments"]
            names = {a["name"] for a in assigns}
            insert_at = next(i for i, a in enumerate(assigns) if a["name"] == "assembly_mode")
            for na in NEW_ASSIGNMENTS:
                if na["name"] not in names:
                    assigns.insert(insert_at, na)
                    insert_at += 1
                    names.add(na["name"])

    WF.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Patched {WF}")


if __name__ == "__main__":
    main()
