# XMUM Moodle Agent Modern UI Design

## Goal

Refresh the PySide6 desktop UI with a modern Windows-friendly style: solid top title background, right-aligned window controls, Source Han Serif typography, unified subpage styling, button animations, and a moving glass-light backdrop.

## Direction

Use the approved B direction with these refinements:

- Keep the title bar visually integrated with the window surface.
- Place minimize and close controls at the top right without boxed borders.
- Use Source Han Serif first, then fall back to SimSun and common Chinese serif fonts.
- Apply one shared component language to home, courses, notes, login, and API settings.
- Give every button hover and press feedback. Hover should gradually shift color; press should briefly scale down with a spring-like feel.
- Add two slow moving light sources behind the translucent window container to create a subtle frosted-glass ambience.

## Architecture

Keep the implementation inside the existing PySide6 GUI module. Add focused custom widgets for reusable interaction effects:

- `AnimatedButton` handles hover color transitions and press scale feedback.
- `LightBackdrop` paints the moving background lights behind the main container.
- `TitleBar` owns right-aligned minimize and close buttons.

The rest of the UI keeps the existing page classes and signal wiring, replacing plain buttons where practical and centralizing styling through the app stylesheet.

## Testing

Automated tests should verify that the new widget classes exist, title controls are right aligned by construction, and key buttons use animated button behavior. Existing GUI state and action tests should continue passing.
