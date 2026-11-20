/* Pure logic shared by the UI and dependency-free Node tests. */
(function (root) {
  'use strict';
  class Stabilizer {
    constructor(required = 3) { this.required = required; this.reset(); }
    reset() { this.label = null; this.count = 0; }
    push(prediction) {
      if (!['OK','REVIEW'].includes(prediction.status) || !prediction.label) { this.reset(); return {ready: false, count: 0, prediction}; }
      if (this.label === prediction.label) this.count++; else { this.label = prediction.label; this.count = 1; }
      return {ready: this.count >= this.required, count: this.count, prediction};
    }
  }
  function cameraError(error) {
    const errors = {
      NotAllowedError: 'Camera permission denied. In Chrome/Edge: site controls → Camera → Allow; also check Windows Settings → Privacy & security → Camera.',
      NotFoundError: 'No camera found. Reconnect the USB camera, then refresh the device list.',
      NotReadableError: 'Camera is occupied or unavailable. Close Camera, Zoom, Teams or another browser tab and retry.',
      OverconstrainedError: 'The selected device is unavailable. Refresh the camera list and choose the device again.',
      SecurityError: 'Use http://localhost:8000 on this laptop. LAN HTTP pages cannot access the camera.',
      AbortError: 'Camera startup was interrupted. Select the device and retry.'
    };
    return errors[error.name] || 'Camera could not start. Reconnect the device and check browser/Windows permissions.';
  }
  function size(bytes) { return bytes >= 1048576 ? (bytes / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(bytes / 1024)) + ' KB'; }
  const api = {Stabilizer, cameraError, size};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AgriCore = api;
})(typeof window !== 'undefined' ? window : globalThis);
