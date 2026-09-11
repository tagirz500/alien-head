r"""Alien page, phone as camera: scan once (phone opens camera.html?cam=CODE), PC tracks the face; then Stop/Start, a PC
reload and a phone reload must all relink with the same code and no new scan.   python alien_relink_test.py [base]"""
import asyncio, os, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8768/"
PHONE_ARGS = ["--autoplay-policy=no-user-gesture-required", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--use-file-for-fake-video-capture=" + os.path.join(HERE, "faceclip.y4m")]
PC_ARGS = ["--enable-gpu", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"]
LINKED = "!document.getElementById('camlink') && !!document.getElementById('cam').srcObject && document.getElementById('cam').srcObject.active"
FACE = "/face yes/.test(document.getElementById('hud').textContent)"
CODE = "/^\\d{3}$/.test(document.getElementById('camCode')?.textContent || '')"
async def wait(pg, js, n=60):
    for _ in range(n):
        if await pg.evaluate(js): return True
        await pg.wait_for_timeout(500)
    return False
async def run():
    async with async_playwright() as p:
        bPC = await p.chromium.launch(channel="msedge", headless=True, args=PC_ARGS); bPH = await p.chromium.launch(channel="msedge", headless=True, args=PHONE_ARGS)
        pc = await bPC.new_page(viewport={"width": 1000, "height": 700}); ph = await bPH.new_page(viewport={"width": 390, "height": 800})
        errs = []; pc.on("pageerror", lambda e: errs.append("pc: " + str(e))); ph.on("pageerror", lambda e: errs.append("phone: " + str(e)))
        await pc.goto(BASE + "?cam"); await wait(pc, CODE); code = await pc.text_content("#camCode"); print("1 PC code", code)
        await ph.goto(BASE + "camera.html?cam=" + code)
        ok = await wait(pc, LINKED) and await wait(pc, FACE, 90); print("2 linked + face tracked:", ok, "|", await pc.text_content("#hud"), "| phone:", await ph.text_content("#status"))
        await pc.screenshot(path=os.path.join(HERE, "alien_phonecam.png"))
        await pc.click("#start"); await pc.wait_for_timeout(700); await pc.click("#start")
        ok = await wait(pc, LINKED, 30) and await wait(pc, FACE, 90); print("3 stop/start:", ok, "| overlay:", await pc.evaluate("!!document.getElementById('camlink')"))
        await pc.reload(); await wait(pc, CODE); code2 = await pc.text_content("#camCode")
        ok = await wait(pc, LINKED, 80) and await wait(pc, FACE, 90); print("4 PC reload: same code", code2 == code, "| relinked:", ok, "| phone:", await ph.text_content("#status"))
        await ph.reload(); ok = await wait(pc, LINKED, 80); await pc.wait_for_timeout(2000); print("5 phone reload: relinked:", ok, "| face:", await pc.evaluate(FACE))
        print("errors:", errs[:5] or "none"); await bPC.close(); await bPH.close()
asyncio.run(run())
