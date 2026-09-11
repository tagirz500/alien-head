# Alien Head

A rigged alien bust (Sketchfab "Sectoid" model) driven by your head, face and shoulders from a webcam, in the browser.
Live: https://tagirz500.github.io/alien-head/

- Face: MediaPipe Face Landmarker gives the head's rotation and position (facial transformation matrix) and eye-gaze blendshapes.
- Shoulders: MediaPipe Pose Landmarker lite; the shoulder line rolls and turns the whole bust.
- Phone as camera: the PC shows a 3-digit code and a QR; the phone opens `camera.html`, streams its camera over WebRTC (PeerJS broker, no server), and the tracking runs on the PC.
- Everything is in `docs/` (GitHub Pages). `alien.glb` was exported from the FBX with Blender.
