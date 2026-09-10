# Overview

I have zero experience in UI design and color theory, but I do have a nice book about colors (*a dictionary of color combinations*) and I like looking at pleasant and interesting color combinations. In Jobsies, the philosiphy is following:

  - 3 main colors, with following goals:
    - `--primary` - serves as a background color for the sidebar. Derived colors are lighter for the main content background (`--content-main-bg`) and darker for the page background (`--content-second-bg`)
    - `--secondary` - serves as a color for titles and hover for action buttons and icons
    - `--tertiary` - serves as background color for active page icon



## Backup light theme

```css
:root[data-theme="light"] {
  /* Primary colors of the theme,
  uses as a background of the menu, title texts
  and highlighted menu icon*/
  /* --primary: #B8B8AA;
  --secondary: #41433c;
  --tertiary: #586F6B; */

  --primary: #d1b0a7;
  --secondary: #40456a;
  --tertiary: #0093a5;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.1);
  --shadow-light: rgba(0, 0, 0, 0.06);
  --overlay-backdrop: rgba(0, 0, 0, 0.5);
  --shadow-lightest: rgba(0, 0, 0, 0.04);

  /* Text */
  --text-main: #292c25;
  --text-subtle: #303030;
  --text-title: var(--secondary);
  --text-title-shadow: #444f4a;

  /* Content Block */
  --content-main-bg: #eeeeeb;
  --content-second-bg: #959587;
  --content-widget-bg: #f9f9f7;
  --content-hover-bg: #f3f4f6;
  --content-border-subtle: #d1d5db;
  --content-action-text: var(--text-primary);
  --content-action-hover: #7F9183;

  /* Sidebar Block */
  --sidebar-bg: var(--primary);
  --sidebar-icon-bg-active: var(--tertiary);
  --sidebar-icon-bg-hover: #7F9183;
  --sidebar-icon-color-active: #ffffff;

  /* Table */
  --row: var(--content-widget-bg);
  --row-hover: var(--content-main-bg);

  /* Negative and positive interactions */
  --negative-main: #991b1b;
  --negative-dim: #fee2e2;
  --positive-main: #065f46;
  --positive-dim: #d1fae5;
}
```