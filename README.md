# handyaddons.com

The website for handyaddons — add-ons for Google Sheets.

## How a change reaches the live site

1. Edit the text in `build.py`.
2. Commit the change on GitHub.
3. GitHub Actions runs `build.py`, checks the result and publishes it.

The whole cycle takes a minute or two. The Actions tab shows a green tick when
it worked and a red cross when it did not — and if it did not, the previous
version of the site stays up, so a mistake cannot take the site down.

## Where things live

| What | Where |
|---|---|
| All page texts | `build.py` |
| Per-add-on facts (permissions, limitations, uninstall) | the `ADDONS` list at the top of `build.py` |
| Styles | `site/assets/css/site.css` |
| Behaviour: gallery, animations, back-to-top | `site/assets/js/site.js` |
| Screenshots | `site/assets/screenshots/` |
| Logos and icons | `site/assets/brand/` |
| Generated pages | `site/**/*.html` — do not edit by hand, they are overwritten |

## Addresses

| Address | Built from |
|---|---|
| handyaddons.com | `index.html`, redirects to the Cell Editor page |
| handyaddons.com/cell-editor/ | the landing page |
| handyaddons.com/cell-editor/privacy/ | one privacy policy per add-on |
| handyaddons.com/terms/ | shared by every add-on |
| handyaddons.com/support/ | shared by every add-on |

`/cell-editor/` is permanent: the add-on's own Help window links there.

## Adding a second add-on

Append a dictionary to `ADDONS` in `build.py`. From it the script generates that
add-on's privacy policy at its own address, its block in the shared terms, its
row on the support page and its entry in the sitemap.

## When Google issues a Marketplace link

Set `MARKETPLACE_URL` near the top of `build.py`. Every install button on the
site turns from a grey label into a live button at once.

## Adding the video

In `build.py`, find the commented-out block marked `VIDEO SECTION` and follow
the note inside it.

## Files that must not be deleted

- `site/CNAME` — holds the domain name.
- `site/.nojekyll` — stops GitHub processing the files as a blog.
- `.github/workflows/deploy.yml` — the build and publish step itself.
