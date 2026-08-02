# Cerebro TUI Keyboard Shortcuts

Complete reference for keyboard shortcuts in the Cerebro Text User Interface.

## Global Navigation

These shortcuts work from any screen:

| Key | Action | Description |
|-----|--------|-------------|
| `d` | Dashboard | Jump to Dashboard screen |
| `p` | Projects | Jump to Projects screen |
| `i` | Intelligence | Jump to Intelligence screen |
| `s` | Scripts | Jump to Scripts screen |
| `g` | GCP Credits | Jump to GCP Credits screen |
| `l` | Logs | Jump to Logs screen |
| `?` | Help | Show help screen |
| `q` | Quit | Exit the application |

## Universal Shortcuts

These work on most screens:

| Key | Action | Description |
|-----|--------|-------------|
| `r` | Refresh | Reload current screen data |
| `/` | Search | Focus search/filter input (where available) |
| `Esc` | Back | Go back or exit current screen |
| `Tab` | Next Field | Move to next input field |
| `Shift+Tab` | Previous Field | Move to previous input field |
| `Enter` | Submit | Submit form or execute action |

## Screen-Specific Shortcuts

### Dashboard (d)

| Key | Action | Description |
|-----|--------|-------------|
| `s` | Quick Scan | Execute quick project scan |
| `r` | Refresh | Refresh system metrics |

**Features:**
- Auto-refreshes every 10 seconds
- Real-time system health monitoring
- One-click actions for common tasks

---

### Projects (p)

| Key | Action | Description |
|-----|--------|-------------|
| `/` | Filter | Focus search input to filter projects |
| `r` | Refresh | Reload project list |
| `↑` `↓` | Navigate | Navigate through project rows |
| `Enter` | Select | View selected project details |

**Features:**
- Live search filtering
- Sortable columns (click headers)
- Color-coded health scores
- Handles 1000+ projects efficiently

---

### Intelligence (i)

| Key | Action | Description |
|-----|--------|-------------|
| `Ctrl+Q` | Focus Query | Focus the query input field |
| `Enter` | Execute | Execute the query |
| `Tab` | Mode Toggle | Switch between Semantic/Exact modes |

**Features:**
- Query history saved across sessions
- Mode preference remembered
- Real-time progress tracking
- Formatted results display

---

### Scripts (s)

| Key | Action | Description |
|-----|--------|-------------|
| `Click` | Select | Select command group or command |
| `Enter` | Execute | Run selected command |
| `Esc` | Cancel | Return to command selection |

**Features:**
- 24 CLI commands organized in 7 groups
- Real-time progress bars
- Live output streaming
- Command execution history

---

### GCP Credits (g)

| Key | Action | Description |
|-----|--------|-------------|
| `r` | Refresh | Refresh credit information |
| `Tab` | Next Field | Move between queries/workers inputs |
| `Enter` | Start Burn | Execute batch burn |

**Features:**
- Real-time credit tracking
- Burn progress monitoring
- Automatic credit refresh after operations
- Burn history tracking

---

### Logs (l)

| Key | Action | Description |
|-----|--------|-------------|
| `p` | Pause/Resume | Toggle log tail pause |
| `c` | Clear | Clear all logs |
| `Click` | Filter | Click level buttons to filter |
| `Type` | Module Filter | Type in module filter to narrow logs |

**Features:**
- Live log tail
- Multi-level filtering (INFO/WARNING/ERROR)
- Module name filtering
- Color-coded log levels
- Ring buffer (max 1000 logs)

---

### Help Screen (?)

| Key | Action | Description |
|-----|--------|-------------|
| `Esc` | Close | Close help and return to previous screen |
| `q` | Close | Close help and return to previous screen |
| `Scroll` | Navigate | Use scroll or arrow keys to read |

**Features:**
- Complete keyboard reference
- Feature guide by screen
- Tips and tricks
- Version information

---

## Mouse Support

The TUI also supports mouse interactions:

| Action | Description |
|--------|-------------|
| Click buttons | Execute button actions |
| Click input fields | Focus input fields |
| Click table rows | Select rows in DataTables |
| Scroll | Scroll through content |
| Click sidebar | Navigate to different screens |

---

## Tips for Efficient Navigation

1. **Master the letter keys:** `d`, `p`, `i`, `s`, `g`, `l` for instant screen switching
2. **Use `/` for quick filtering:** Available on Projects and Logs screens
3. **Press `?` when in doubt:** Quick access to help from anywhere
4. **Leverage `r` for freshness:** Manually refresh any screen
5. **Tab through forms:** Faster than mouse for input fields
6. **Esc is universal:** Always goes back or exits
7. **Watch the footer:** Shows available shortcuts for current context

---

## Keyboard Accessibility

The TUI is fully keyboard accessible:

- ✅ All features accessible via keyboard
- ✅ Logical tab order through interactive elements
- ✅ Visual focus indicators
- ✅ Consistent shortcut patterns across screens
- ✅ Help always one key away (`?`)

---

## Quick Reference Card

**Print this for quick reference:**

```
GLOBAL:  d=Dashboard p=Projects i=Intelligence s=Scripts g=GCP l=Logs ?=Help q=Quit
COMMON:  r=Refresh /=Search Esc=Back Tab=Next Enter=Submit
SCREEN:  Varies by screen (see help with ?)
```

---

## Customization

Currently, keyboard shortcuts are fixed. Custom keybindings are planned for a future release.

**Planned features:**
- User-configurable shortcuts
- Vim-mode navigation
- Custom action macros
- Keyboard shortcut profiles

---

## Troubleshooting

**Shortcuts not working?**
1. Ensure TUI window has focus
2. Check you're not in an input field (press Esc first)
3. Some shortcuts are screen-specific - check help (?)

**Mouse not working?**
1. Ensure terminal supports mouse input
2. Try updating your terminal emulator
3. Keyboard shortcuts work in all terminals

---

**For more information:**
- User Guide: `PHASE3_QUICK_START.md`
- Implementation Details: `PHASE3_IMPLEMENTATION_COMPLETE.md`
- General Help: Press `?` in the TUI

**Version:** Phase 4 Complete
**Last Updated:** 2026-02-03
