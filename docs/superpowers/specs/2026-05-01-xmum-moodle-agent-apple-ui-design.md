# XMUM Moodle Agent Apple UI Design

## Goal

Refresh the existing Tkinter desktop GUI so it feels like a native Apple utility: calm, white, spacious, and system-like. The app should keep the current Moodle login, course selection, download, and model API workflows unchanged while improving visual polish and adding a Xiamen University icon for the generated Windows executable.

## Approved Direction

Use the "Native Apple Utility" direction from the visual companion. This means:

- White surfaces as the dominant visual language.
- A soft Apple-style application background using `#f5f5f7`.
- Minimal decoration, restrained shadows, and quiet dividers.
- Apple blue `#0071e3` for primary actions.
- Neutral text colors close to Apple system grays: `#1d1d1f`, `#6e6e73`, and `#86868b`.
- XMUM/XMU identity appears through the window/app icon and a compact brand mark, not through a red-heavy interface.

## UI Structure

The app keeps its current three-view structure:

- Home: a centered welcome view with the app name, a short Moodle workflow hint, and one primary login button.
- Courses: a left navigation shell with a right-side course management page, semester selector, course count summary, course table, select-all control, open-folder action, and download action.
- Notes: a settings-style page for model API status, provider selection, and note generation controls.

The left sidebar remains because it matches the current app architecture and gives the desktop UI a stable, Settings-like feel. It should look lighter and more native: pale gray surface, compact brand mark, rounded active item, and clear disabled states before login.

## Components

### Shell

The root window uses a white and light-gray composition:

- App background: `#f5f5f7`.
- Sidebar: `#f2f2f7` or a close neutral.
- Main content: `#ffffff` panels on the light background.
- Status bar: subtle rounded or bordered strip, not a saturated banner.

### Buttons

Primary actions use Apple blue with white text and a pressed/disabled state:

- Login Moodle
- Download selected courses
- Save API settings when it is the main action in a dialog

Secondary actions stay white or light gray with dark text:

- Open download directory
- Cancel
- Save configuration when it is not the primary workflow action

### Forms And Dialogs

Login and API settings windows should use the same visual system as the main window:

- White panels.
- Larger padding than the current UI.
- Visible labels above fields.
- Clear disabled states.
- Dialog sizes tall enough to avoid clipping action buttons.

### Course List

The course table should feel closer to a Finder or Settings list:

- Light header.
- Soft row selection.
- Thin separators.
- Consistent row height.
- Checkbox column stays stable and narrow.

## App Icon

Add a reusable asset location, preferably `src/xmum_moodle_agent/assets/`, containing a Xiamen University `.ico` file. The implementation should set the icon in two places:

- Runtime window icon for Tkinter.
- PyInstaller `icon=` option in the executable `.spec` file.

If an official `.ico` is not already available in the repository, create a clean local icon asset that represents Xiamen University/XMUM without changing the UI implementation contract. The file path should be stable so tests and packaging can verify it.

## Constraints

- Do not change login, Moodle discovery, download, file indexing, or note generation logic.
- Keep the UI base white.
- Keep text readable at the existing minimum window size.
- Avoid decorative gradients, large illustrations, emoji icons, and marketing-page hero treatment.
- Do not introduce a new GUI framework; stay with Tkinter/ttk.
- Work with the existing dirty tree without reverting unrelated changes.

## Testing

Add focused tests where the implementation is deterministic:

- The GUI exposes the expected Apple-style theme colors or style constants.
- The app icon path exists.
- The PyInstaller spec includes the icon path.
- Existing layout tests continue to pass, especially the login dialog height test.

Manual verification should include launching the GUI locally and checking the home, courses, notes, login, and API settings surfaces at the minimum window size.
