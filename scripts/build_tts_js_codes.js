#!/usr/bin/env node
/**
 * Generates JSON-escaped jsCode strings for DV001 TTS Code nodes.
 * Run: node scripts/build_tts_js_codes.js
 */
const fs = require('fs');
const path = require('path');

function body(TTS_ROLE, TTS_CUT) {
  return `// Multi-provider TTS (elevenlabs | openai | azure | google). Same emotional posture → voice map.
const TTS_ROLE = ${JSON.stringify(TTS_ROLE)};
const TTS_CUT = ${JSON.stringify(TTS_CUT)};
const cfg = $('Set Global Config').first().json;
const sel = $('🌅 Select Background Loop').first().json;
const vo = $('✍️ Voice Writer Agent').first().json.output;
const provider = (cfg.tts_provider || sel.tts_provider || 'elevenlabs').toLowerCase().trim();
const energy = sel.hook_energy || sel.emotional_posture || 'anchor';

function escapeXml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function defOpenAi(role, e) {
  const H = { anchor: 'alloy', fire: 'echo', shepherd: 'nova', challenger: 'onyx' };
  const R = { anchor: 'shimmer', fire: 'fable', shepherd: 'nova', challenger: 'ash' };
  const m = role === 'reflection' ? R : H;
  return m[e] || m.anchor;
}

function defAzure(role, e) {
  const H = {
    anchor: 'en-US-GuyNeural',
    fire: 'en-US-DavisNeural',
    shepherd: 'en-US-JasonNeural',
    challenger: 'en-US-EricNeural',
  };
  const R = {
    anchor: 'en-US-JennyNeural',
    fire: 'en-US-AriaNeural',
    shepherd: 'en-US-SaraNeural',
    challenger: 'en-US-MichelleNeural',
  };
  const m = role === 'reflection' ? R : H;
  return m[e] || m.anchor;
}

function defGoogle(role, e) {
  const H = {
    anchor: { languageCode: 'en-US', name: 'en-US-Neural2-D' },
    fire: { languageCode: 'en-US', name: 'en-US-Neural2-J' },
    shepherd: { languageCode: 'en-US', name: 'en-US-Neural2-C' },
    challenger: { languageCode: 'en-US', name: 'en-US-Neural2-I' },
  };
  const R = {
    anchor: { languageCode: 'en-US', name: 'en-US-Neural2-F' },
    fire: { languageCode: 'en-US', name: 'en-US-Neural2-G' },
    shepherd: { languageCode: 'en-US', name: 'en-US-Neural2-E' },
    challenger: { languageCode: 'en-US', name: 'en-US-Neural2-H' },
  };
  const m = role === 'reflection' ? R : H;
  return m[e] || m.anchor;
}

let text = '';
if (TTS_ROLE === 'host' && TTS_CUT === 'full') {
  text = vo.full_episode?.host_script || vo.full_narration || '';
} else if (TTS_ROLE === 'reflection' && TTS_CUT === 'full') {
  text = vo.full_episode?.reflection_script || '';
} else if (TTS_ROLE === 'host' && TTS_CUT === 'short') {
  text = [vo.short_cut?.host_script, vo.short_cut?.host_close].filter(Boolean).join(' ').trim();
} else {
  text = vo.short_cut?.reflection_script || '';
}
text = String(text || '').trim();
if (!text) throw new Error('TTS: empty script for ' + TTS_ROLE + ' ' + TTS_CUT);

let audioBuf;
const outName =
  TTS_ROLE === 'host' && TTS_CUT === 'full'
    ? 'host.mp3'
    : TTS_ROLE === 'reflection' && TTS_CUT === 'full'
      ? 'reflection.mp3'
      : TTS_ROLE === 'host'
        ? 'host_short.mp3'
        : 'reflection_short.mp3';

if (provider === 'elevenlabs') {
  const key = cfg.elevenlabs_api_key;
  if (!key) throw new Error('TTS elevenlabs: missing elevenlabs_api_key');
  const voiceId =
    TTS_ROLE === 'host' ? sel.host_voice_id || cfg.elevenlabs_voice_id : sel.reflection_voice_id || cfg.elevenlabs_reflection_voice_id;
  let stability = TTS_ROLE === 'reflection' ? 0.6 : 0.5;
  let similarity = TTS_ROLE === 'reflection' ? 0.8 : 0.75;
  let style = TTS_ROLE === 'reflection' ? 0.15 : 0.2;
  if (TTS_CUT === 'short' && TTS_ROLE === 'host') {
    stability = 0.55;
    similarity = 0.75;
    style = 0;
  }
  if (TTS_CUT === 'short' && TTS_ROLE === 'reflection') {
    stability = 0.6;
    similarity = 0.8;
    style = 0;
  }
  const raw = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://api.elevenlabs.io/v1/text-to-speech/' + voiceId,
    headers: {
      'xi-api-key': key,
      'Content-Type': 'application/json',
      Accept: 'audio/mpeg',
    },
    body: {
      text,
      model_id: 'eleven_turbo_v2_5',
      voice_settings: { stability, similarity_boost: similarity, style, use_speaker_boost: true },
    },
    json: true,
    encoding: 'arraybuffer',
  });
  audioBuf = Buffer.from(raw);
} else if (provider === 'openai') {
  const key = cfg.openai_api_key || cfg.openai_tts_api_key;
  if (!key) throw new Error('TTS openai: set OPENAI_API_KEY (openai_api_key on config)');
  const override = TTS_ROLE === 'host' ? cfg.openai_voice_host : cfg.openai_voice_reflection;
  const voiceName = (override && String(override).trim()) || defOpenAi(TTS_ROLE, energy);
  const model = cfg.openai_tts_model || 'gpt-4o-mini-tts';
  const raw = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://api.openai.com/v1/audio/speech',
    headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      voice: voiceName,
      input: text,
      response_format: 'mp3',
    }),
    encoding: 'arraybuffer',
  });
  audioBuf = Buffer.from(raw);
} else if (provider === 'azure') {
  const key = cfg.azure_speech_key;
  const region = String(cfg.azure_speech_region || 'eastus').trim();
  if (!key) throw new Error('TTS azure: set AZURE_SPEECH_KEY');
  const override = TTS_ROLE === 'host' ? cfg.azure_voice_host : cfg.azure_voice_reflection;
  const voiceName = (override && String(override).trim()) || defAzure(TTS_ROLE, energy);
  const ssml =
    "<speak version='1.0' xml:lang='en-US'><voice xml:lang='en-US' name='" +
    voiceName +
    "'>" +
    escapeXml(text) +
    '</voice></speak>';
  const raw = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://' + region + '.tts.cognitiveservices.azure.com/cognitiveservices/v1',
    headers: {
      'Ocp-Apim-Subscription-Key': key,
      'Content-Type': 'application/ssml+xml',
      'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
      'User-Agent': 'WalkWithMe-n8n',
    },
    body: ssml,
    encoding: 'arraybuffer',
  });
  audioBuf = Buffer.from(raw);
} else if (provider === 'google') {
  const key = cfg.google_tts_api_key;
  if (!key) throw new Error('TTS google: set GOOGLE_TTS_API_KEY');
  let voice = defGoogle(TTS_ROLE, energy);
  const rawOverride = TTS_ROLE === 'host' ? cfg.google_voice_host_json : cfg.google_voice_reflection_json;
  if (rawOverride && String(rawOverride).trim()) {
    try {
      voice = JSON.parse(String(rawOverride).trim());
    } catch (e) {
      throw new Error('TTS google: invalid google_voice_*_json (expect {languageCode,name})');
    }
  }
  const r = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://texttospeech.googleapis.com/v1/text:synthesize?key=' + encodeURIComponent(key),
    headers: { 'Content-Type': 'application/json' },
    body: {
      input: { text },
      voice: { languageCode: voice.languageCode, name: voice.name },
      audioConfig: { audioEncoding: 'MP3', speakingRate: 1.0 },
    },
    json: true,
  });
  if (!r.audioContent) throw new Error('TTS google: no audioContent');
  audioBuf = Buffer.from(r.audioContent, 'base64');
} else {
  throw new Error('Unknown tts_provider: ' + provider + ' (use elevenlabs|openai|azure|google)');
}

const bin = await this.helpers.prepareBinaryData(audioBuf, outName, 'audio/mpeg');
return [
  {
    json: { tts_provider: provider, tts_segment: TTS_ROLE + '_' + TTS_CUT, tts_out: outName },
    binary: { data: bin },
  },
];
`;
}

const out = {
  host_full: body('host', 'full'),
  reflection_full: body('reflection', 'full'),
  host_short: body('host', 'short'),
  reflection_short: body('reflection', 'short'),
};
const dest = path.join(__dirname, '..', 'n8n', 'code', 'generated_tts_codes.json');
fs.writeFileSync(dest, JSON.stringify(out, null, 2), 'utf8');
console.log('Wrote', dest);
