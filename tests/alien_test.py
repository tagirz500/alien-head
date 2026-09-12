r"""Alien head page with a fake camera (a face still, and its mirror image): face + shoulders found, head bones move
with the tracked pose, yaw flips sign on the mirrored clip, ?cam shows a code + QR.   python alien_test.py [base url]"""
import asyncio, os, sys, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8768/"
def args(clip): return ["--enable-gpu", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--use-file-for-fake-video-capture=" + os.path.join(HERE, clip)]
READ = """() => { const a = window.alien, t = a.track, q = b => b ? b.quaternion.toArray().map(v => +v.toFixed(3)) : null;
  return { face: t.haveFace, shoulders: t.haveShoulders, ms: Math.round(t.ms), yaw: +t.yawDeg.toFixed(1), pitch: +t.pitchDeg.toFixed(1), roll: +t.rollDeg.toFixed(1),
           head: q(a.rig.head), neck: q(a.rig.neck), root: q(a.rig.root), eyes: a.rig.eyes.length, gaze: t.gaze.map(v => +v.toFixed(2)), shoulder: {roll: +(t.shoulder.roll*57.3).toFixed(1), yaw: +(t.shoulder.yaw*57.3).toFixed(1)},
           armsShown: a.arms.parts.filter(m => m.visible).length, bodyPos: a.model.position.toArray().map(x=>+x.toFixed(2)), hud: document.getElementById('hud').textContent, error: document.getElementById('error').textContent, status: document.getElementById('status').textContent }; }"""
async def run_clip(p, clip, tag):
    b = await p.chromium.launch(channel="msedge", headless=True, args=args(clip))
    pg = await b.new_page(viewport={"width": 1000, "height": 700}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text[:140]) if m.type == "error" and "favicon" not in m.text else None)
    await pg.goto(BASE + "?t=" + tag); await pg.wait_for_timeout(2500)
    await pg.click("#start")
    for _ in range(80):
        await pg.wait_for_timeout(500)
        if await pg.evaluate("window.alien.track.haveFace"): break
    await pg.wait_for_timeout(1500)
    neutral = await pg.evaluate(READ)                      # auto-centred on the first face: everything ~0
    if not neutral['face']: print(f'== {tag}: NO FACE', json.dumps(neutral)[:600], '| errors:', errs[:5]); await pg.screenshot(path=os.path.join(HERE, f'alien_{tag}.png')); await b.close(); return neutral, neutral
    # pretend the head turned: feed a rotated neutral (turn the neutral 20 deg the other way) and read the bones
    await pg.evaluate("() => { const a = window.alien, THREE_Q = a.track.neutralQ; const e = new (THREE_Q.constructor)(); a.track.neutralQ = THREE_Q.clone().multiply(new THREE_Q.constructor().setFromAxisAngle({x:0,y:1,z:0,isVector3:true}, -20*Math.PI/180)); }")
    await pg.wait_for_timeout(600)
    turned = await pg.evaluate(READ)
    await pg.screenshot(path=os.path.join(HERE, f"alien_{tag}.png"))
    print(f"== {tag}: arms {neutral['armsShown']} body {neutral['bodyPos']} | neutral yaw/pitch/roll {neutral['yaw']}/{neutral['pitch']}/{neutral['roll']} face {neutral['face']} shoulders {neutral['shoulders']} ms {neutral['ms']} eyes {neutral['eyes']} shoulder {neutral['shoulder']} gaze {neutral['gaze']}")
    print(f"   after a 20° head turn: yaw {turned['yaw']} | head bone moved: {turned['head'] != neutral['head']} | neck moved: {turned['neck'] != neutral['neck']} | hud: {turned['hud']!r}")
    print("   errors:", errs[:5] or "none")
    await b.close(); return neutral, turned
async def run():
    async with async_playwright() as p:
        a = await run_clip(p, "faceclip.y4m", "plain"); f = await run_clip(p, "faceclip_flip.y4m", "flip")
        print("mirror check: the mirrored picture gives the opposite raw shoulder roll:", a[0]["shoulder"], "vs", f[0]["shoulder"])
        # ?cam: code + QR
        b = await p.chromium.launch(channel="msedge", headless=True, args=args("faceclip.y4m")); pg = await b.new_page(viewport={"width": 1000, "height": 700})
        await pg.goto(BASE + "?cam")
        for _ in range(30):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("/^\\d{3}$/.test(document.getElementById('camCode')?.textContent || '')"): break
        print("?cam: code", await pg.text_content("#camCode"), "| qr drawn:", await pg.evaluate("!!document.querySelector('#camQr canvas, #camQr img')"), "| url:", await pg.text_content("#camUrl"))
        await pg.screenshot(path=os.path.join(HERE, "alien_cam_qr.png")); await b.close()
asyncio.run(run())
