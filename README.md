# handover: Mia collection page and gifting page handover (HTML)

Open `index.html` (or serve the folder). Two page tabs, **Collection page** and **Gifting page**. Each has two views:
- **Section by journey stage:** every section grouped by where it sits in the shopper's journey, with why it is there.
- **Developer handover:** sections at a glance (priority and status), then each section's purpose, core logic, what the team can change, where it goes and edge cases.

Every section has its frames, collapsed, in `assets/frames/` (collection) and `assets/frames/gifting/` (gifting), loaded only when opened.
The gifting page uses the live site's existing header and footer; the ones in its frames are for reference only. Bag and checkout are out of scope.

`_build/build_handover.py` produced the collection page. The gifting tab and the trims were applied directly to `index.html`.

Figma: collection https://www.figma.com/design/qGeAfcHPwMm86maQRkLyvt/Mia---Collection-Page?node-id=49-2 , gifting https://www.figma.com/design/Xu5zTr1mxGPVWxEVjJvJnG/Gifting-Page
