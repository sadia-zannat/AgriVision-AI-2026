/* Browser capture owns the physical device. Never silently use a default camera. */
(function (root) {
  'use strict';
  class CameraController {
    constructor(video, mediaDevices, onDisconnect = () => {}) {
      this.video = video; this.devices = mediaDevices; this.stream = null; this.paused = false; this.generation = 0;
      this.onDisconnect = onDisconnect; this.activeId = '';
    }
    async enumerate(grant = false) {
      if (!this.devices?.getUserMedia) throw Object.assign(new Error('Secure context required'), {name: 'SecurityError'});
      if (grant && !this.stream) {
        const probe = await this.devices.getUserMedia({video: true, audio: false});
        // Permission only. This unnamed/default stream is never used for monitoring.
        probe.getTracks().forEach(track => track.stop());
      }
      const list = await this.devices.enumerateDevices();
      return list.filter(d => d.kind === 'videoinput' && d.deviceId && d.deviceId !== 'default');
    }
    async start(deviceId) {
      if (!deviceId) throw Object.assign(new Error('Select a device'), {name: 'OverconstrainedError'});
      this.stop(); const generation = ++this.generation;
      const stream = await this.devices.getUserMedia({audio: false, video: {
        deviceId: {exact: deviceId}, width: {ideal: 1280}, height: {ideal: 720}, frameRate: {ideal: 24, max: 30}
      }});
      if (generation !== this.generation) { stream.getTracks().forEach(t => t.stop()); return null; }
      const track = stream.getVideoTracks()[0];
      const actual = track.getSettings().deviceId;
      if (actual && actual !== deviceId) { stream.getTracks().forEach(t => t.stop()); throw Object.assign(new Error('Device mismatch'), {name: 'OverconstrainedError'}); }
      this.stream = stream; this.activeId = actual || deviceId; this.video.srcObject = stream; this.paused = false;
      track.addEventListener('ended', () => { if (this.stream === stream) { this.stop(); this.onDisconnect(); } });
      await this.video.play();
      return {label: track.label || 'Unnamed camera', deviceId: this.activeId, settings: track.getSettings()};
    }
    pause() { if (this.stream) { this.video.pause(); this.paused = true; } }
    async resume() { if (this.stream) { await this.video.play(); this.paused = false; } }
    stop() {
      this.generation++; const stream = this.stream; this.stream = null; this.activeId = ''; this.paused = false;
      if (stream) stream.getTracks().forEach(t => t.stop());
      this.video.pause(); this.video.srcObject = null;
    }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = CameraController;
  else root.CameraController = CameraController;
})(typeof window !== 'undefined' ? window : globalThis);
