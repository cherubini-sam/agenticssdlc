/* Agentics SDLC - init.js */

(function () {
  'use strict';

  /* Results modal */

  /* Bare-bones markdown-to-HTML for the results overlay. */
  function mdToHtml(md) {
    if (!md) return '';

    var _c = getThemeColors();
    var codeBg     = '#1E262A';
    var codeBorder = _c.isDark ? 'rgba(133,146,137,0.30)' : 'rgba(133,146,137,0.45)';
    var codeText   = '#D3C6AA';
    var inlineBg   = _c.isDark ? '#2D353B' : '#CFC3A3';
    var inlineText = _c.isDark ? '#D3C6AA' : '#3D4A3D';
    var sepColor   = _c.isDark ? 'rgba(133,146,137,0.35)' : 'rgba(92,107,98,0.40)';

    var escaped = md
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    escaped = escaped.replace(/```[\w]*\n?([\s\S]*?)```/g, function(_, code) {
      return '<pre style="background:' + codeBg + ';border:1px solid ' + codeBorder + ';color:' + codeText + ';border-radius:6px;padding:12px;overflow-x:auto;font-size:12px;line-height:1.5">' + code + '</pre>';
    });
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background:' + inlineBg + ';color:' + inlineText + ';padding:2px 5px;border-radius:3px;font-size:12px">$1</code>');
    escaped = escaped.replace(/^# (.+)$/gm, '<h1 style="font-size:1.4em;margin:16px 0 8px;border-bottom:1px solid ' + sepColor + ';padding-bottom:6px">$1</h1>');
    escaped = escaped.replace(/^## (.+)$/gm, '<h2 style="font-size:1.15em;margin:14px 0 6px">$1</h2>');
    escaped = escaped.replace(/^### (.+)$/gm, '<h3 style="font-size:1em;margin:12px 0 4px">$1</h3>');
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid ' + sepColor + ';margin:12px 0">');
    escaped = escaped.replace(/^[\-\*] (.+)$/gm, '<li style="margin:3px 0">$1</li>');
    escaped = escaped.replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul style="padding-left:20px;margin:6px 0">$&</ul>');
    escaped = escaped.replace(/\n{2,}/g, '</p><p style="margin:8px 0">');
    return '<p style="margin:8px 0">' + escaped + '</p>';
  }

  function showResultsModal(content) {
    var existing = document.getElementById('agentics-results-modal');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.id = 'agentics-results-modal';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.65);display:flex;align-items:center;justify-content:center;padding:16px';

    var _mc = getThemeColors();
    var box = document.createElement('div');
    box.style.cssText = 'background:' + _mc.paperBg + ';border:1px solid ' + _mc.railBg + ';border-radius:12px;padding:28px 32px;width:92vw;max-width:1100px;height:88vh;overflow-y:auto;color:' + _mc.textColor + ';box-shadow:0 12px 48px rgba(0,0,0,0.7);display:flex;flex-direction:column';

    var header = document.createElement('div');
    header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-shrink:0';
    header.innerHTML = '<span style="font-size:1.1em;font-weight:600;color:' + _mc.textColor + '">Agentics SDLC Workflow</span>';

    var closeBtn = document.createElement('button');
    closeBtn.textContent = '\u2715 Close';
    closeBtn.style.cssText = 'background:' + _mc.inputBg + ';color:' + _mc.mutedColor + ';  border:none;border-radius:6px;padding:6px 16px;cursor:pointer;font-size:13px';
    closeBtn.addEventListener('click', function () { overlay.remove(); });
    header.appendChild(closeBtn);

    var body = document.createElement('div');
    body.style.cssText = 'flex:1;overflow-y:auto;font-size:13.5px;line-height:1.65;word-break:break-word';
    body.innerHTML = mdToHtml(content);

    box.appendChild(header);
    box.appendChild(body);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.remove(); });
    document.addEventListener('keydown', function onEsc(e) {
      if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', onEsc); }
    });
  }

  /* Monkey-patch WebSocket */
  (function patchWebSocket() {
    var Orig = window.WebSocket;
    function PatchedWS(url, protos) {
      var ws = (protos !== undefined) ? new Orig(url, protos) : new Orig(url);
      ws.addEventListener('message', function (evt) {
        if (typeof evt.data !== 'string') return;
        // Socket.IO v4 EVENT packet format: "42[\"event_name\",{...}]"
        if (evt.data.charAt(0) !== '4' || evt.data.charAt(1) !== '2') return;
        try {
          var arr = JSON.parse(evt.data.slice(2));
          if (!Array.isArray(arr) || arr[0] !== 'show_results_modal') return;
          var payload = arr[1];
          if (payload && payload.content) showResultsModal(payload.content);
        } catch (_) {}
      });
      return ws;
    }
    PatchedWS.CONNECTING = Orig.CONNECTING;
    PatchedWS.OPEN       = Orig.OPEN;
    PatchedWS.CLOSING    = Orig.CLOSING;
    PatchedWS.CLOSED     = Orig.CLOSED;
    PatchedWS.prototype  = Orig.prototype;
    window.WebSocket = PatchedWS;
  }());

  /* Email auto-fill */
  var DUMMY_EMAIL = 'viewer@agentics.local';

  function fillEmailField() {
    var input = document.querySelector('input[id="email"], input[name="email"], input[type="email"]');
    if (!input) return;
    // Use the native setter so React's synthetic onChange fires properly
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
    if (setter && setter.set) {
      setter.set.call(input, DUMMY_EMAIL);
    } else {
      input.value = DUMMY_EMAIL;
    }
    input.dispatchEvent(new Event('input',  { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }

  /* Hide sidebar toggle */
  function hideEl(el) {
    if (!el) return;
    el.style.visibility = 'hidden';
    el.style.pointerEvents = 'none';
    el.style.width = '0';
    el.style.minWidth = '0';
    el.style.overflow = 'hidden';
    el.style.position = 'absolute';
    el.style.opacity = '0';
  }

  function hideSidebarToggle() {
    hideEl(document.getElementById('open-sidebar-button'));
    hideEl(document.getElementById('close-sidebar-button'));

    ['Open sidebar', 'Close sidebar', 'open sidebar', 'close sidebar',
     'Toggle sidebar', 'toggle sidebar'].forEach(function (label) {
      document.querySelectorAll('[aria-label="' + label + '"]').forEach(hideEl);
    });

    // On narrow viewports Chainlit renders a separate toggle element in #header
    var header = document.getElementById('header');
    if (header && window.innerWidth <= 1056) {
      var children = header.children;
      for (var i = 0; i < children.length; i++) {
        var ch = children[i];
        var style = ch.getAttribute('style') || '';
        if (style.indexOf('absolute') !== -1) continue;
        if (style.indexOf('position: absolute') !== -1) continue;
        if (ch.querySelector('img')) continue;
        if (ch.querySelector('[class*="MuiStack"]') || ch.children.length > 1) continue;
        hideEl(ch);
      }
    }

    // Catch the MUI Sort/Menu icon Chainlit uses on mobile
    document.querySelectorAll('#header button, #header div[role="button"]').forEach(function (btn) {
      var svg = btn.querySelector('svg');
      if (!svg) return;
      svg.querySelectorAll('path').forEach(function (p) {
        var d = p.getAttribute('d') || '';
        if (d.indexOf('M3 18') === 0) hideEl(btn.closest('[class*="MuiBox"], button') || btn);
      });
    });
  }

  /* Hide copy buttons on non-code messages */
  function hideCopyButtons() {
    document.querySelectorAll('.step button').forEach(function (b) {
      if (b.closest('pre')) return; // keep copy on code blocks
      var label = (b.title || b.getAttribute('aria-label') || '').toLowerCase();
      if (label.indexOf('copy') !== -1 || label.indexOf('clipboard') !== -1) {
        b.style.display = 'none';
      }
      var svg = b.querySelector('svg');
      if (svg) {
        svg.querySelectorAll('path').forEach(function (p) {
          var d = p.getAttribute('d') || '';
          if (d.indexOf('M16 1H4c-1.1') === 0 || d.indexOf('M16 1H') === 0) {
            b.style.display = 'none';
          }
        });
      }
    });
  }

  /* GitHub repo link in the header */
  var _githubInjected = false;
  function injectGithubButton() {
    if (_githubInjected) return;
    var header = document.getElementById('header');
    if (!header) return;
    var rightStack = header.querySelector('.MuiStack-root[class*="MuiStack"]');
    if (!rightStack) {
      rightStack = header.lastElementChild;
    }
    if (!rightStack) return;
    if (document.getElementById('agentics-github-btn')) return;

    var btn = document.createElement('a');
    btn.id = 'agentics-github-btn';
    btn.href = 'https://github.com/cherubini-sam/agenticssdlc';
    btn.target = '_blank';
    btn.rel = 'noopener noreferrer';
    btn.style.cssText = 'display:inline-flex;align-items:center;gap:6px;padding:4px 10px;' +
      'border-radius:6px;text-decoration:none;color:inherit;font-size:13px;' +
      'font-family:inherit;opacity:0.75;transition:opacity 0.2s;';
    btn.onmouseover = function() { btn.style.opacity = '1'; };
    btn.onmouseout  = function() { btn.style.opacity = '0.75'; };
    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 98 96" fill="currentColor">' +
      '<path d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 ' +
      '2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867' +
      '-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 ' +
      '4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 ' +
      '1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 ' +
      '5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 ' +
      '46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 ' +
      '13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 ' +
      '0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 ' +
      '11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 ' +
      '33.405-46.691C97.707 22 75.788 0 48.854 0z"/></svg>Repo';
    rightStack.insertBefore(btn, rightStack.firstChild);
    _githubInjected = true;
  }

  /* Theme bridge: publish CSS vars for dark/light detection */
  function applyThemeBridge() {
    var root = document.documentElement;
    var body = document.body;
    var isDark =
      root.getAttribute('data-theme') === 'dark'  ||
      root.getAttribute('data-color-scheme') === 'dark' ||
      body.getAttribute('data-theme') === 'dark'  ||
      root.classList.contains('dark')             ||
      body.classList.contains('dark');

    // Fallback: measure body bg luminance if no explicit attribute is set
    if (!isDark) {
      var bg  = window.getComputedStyle(body).backgroundColor;
      var rgb = bg.match(/\d+/g);
      if (rgb) isDark = (parseInt(rgb[0]) + parseInt(rgb[1]) + parseInt(rgb[2])) / 3 < 128;
    }

    root.style.setProperty('--ag-is-dark', isDark ? '1' : '0');

    if (isDark) {
      root.style.setProperty('--ag-paper',   '#232A2E');
      root.style.setProperty('--ag-border',  'rgba(133,146,137,0.35)');
      root.style.setProperty('--ag-shadow1', 'rgba(0,0,0,0.55)');
      root.style.setProperty('--ag-shadow2', 'rgba(0,0,0,0.30)');
      root.style.setProperty('--ag-ring',    'rgba(255,255,255,0.04)');
    } else {
      root.style.setProperty('--ag-paper',   '#EBE0C0');
      root.style.setProperty('--ag-border',  'rgba(130,145,129,0.40)');
      root.style.setProperty('--ag-shadow1', 'rgba(60,80,60,0.22)');
      root.style.setProperty('--ag-shadow2', 'rgba(60,80,60,0.12)');
      root.style.setProperty('--ag-ring',    'rgba(60,80,60,0.06)');
    }
  }

  /* Tagline between avatar and starter cards */
  var _taglineInjected = false;
  var _taglineLastTheme = null;
  function injectTagline() {
    var bodyBgCheck = window.getComputedStyle(document.body).backgroundColor;
    var rgbCheck = bodyBgCheck.match(/\d+/g);
    var themeNow  = rgbCheck && (parseInt(rgbCheck[0]) + parseInt(rgbCheck[1]) + parseInt(rgbCheck[2])) / 3 < 128 ? 'dark' : 'light';
    if (_taglineInjected && themeNow === _taglineLastTheme) return;
    // Re-inject when theme changes so colors stay correct
    var old = document.getElementById('ag-tagline');
    if (old) old.remove();
    _taglineInjected = false;
    _taglineLastTheme = themeNow;
    var avatar = document.querySelector('img[src*="avatars"]');
    if (!avatar) return;
    var wrap = avatar.parentElement;
    while (wrap && wrap.parentElement && wrap.parentElement !== document.body) {
      wrap = wrap.parentElement;
    }
    if (!wrap) return;
    if (document.getElementById('ag-tagline')) return;

    var tag = document.createElement('p');
    tag.id = 'ag-tagline';
    var bodyBg  = window.getComputedStyle(document.body).backgroundColor;
    var rgbArr  = bodyBg.match(/\d+/g);
    var isDarkT = rgbArr ? (parseInt(rgbArr[0]) + parseInt(rgbArr[1]) + parseInt(rgbArr[2])) / 3 < 128 : true;
    tag.innerHTML = '<strong style="color:#4588d3">Agentics:</strong> ready when you are.';
    tag.style.cssText = [
      'text-align:center',
      'font-size:1.15rem',
      'letter-spacing:0.01em',
      'margin:18px auto 12px',
      'opacity:0.90',
      'font-family:inherit',
      'max-width:480px',
      'color:' + (isDarkT ? '#c8bfb0' : '#4a3520'),
    ].join(';');

    var avatarBox = avatar.closest('[class*="MuiBox"],[class*="MuiStack"]') || avatar.parentElement;
    if (avatarBox && avatarBox.parentElement) {
      avatarBox.parentElement.insertBefore(tag, avatarBox.nextSibling);
    } else {
      wrap.appendChild(tag);
    }
    _taglineInjected = true;
  }

  /* Swap the default user avatar for our brand icon */
  function replaceUserAvatar() {
    var header = document.getElementById('header');
    if (!header) return;
    header.querySelectorAll('.MuiAvatar-root').forEach(function (avatar) {
      if (avatar.querySelector('img')) return;
      var img = document.createElement('img');
      img.src = '/public/favicon.png';
      img.alt = 'Agentics';
      img.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:50%';
      avatar.style.background = 'transparent';
      avatar.style.backgroundColor = 'transparent';
      avatar.innerHTML = '';
      avatar.appendChild(img);
    });
  }

  /* Theme palette helper */
  function getThemeColors() {
    var bodyBg = window.getComputedStyle(document.body).backgroundColor;
    var rgb    = bodyBg.match(/\d+/g);
    var isDark = rgb ? (parseInt(rgb[0]) + parseInt(rgb[1]) + parseInt(rgb[2])) / 3 < 128 : true;
    return {
      isDark    : isDark,
      paperBg   : isDark ? '#232A2E' : '#EBE0C0',
      textColor : isDark ? '#D3C6AA' : '#5C6A72',
      inputBg   : isDark ? '#2D353B' : '#F3EAD3',
      mutedColor: isDark ? '#859289' : '#829181',
      railBg    : isDark ? 'rgba(255,255,255,0.28)' : 'rgba(0,0,0,0.22)',
      menuBg    : isDark ? '#2D353B' : '#EBE0C0',
      BLUE      : '#4588d3'
    };
  }

  /* Settings dialog theme overrides */
  var _lastInjectedTheme = null;

  function buildSettingsCSS(c) {
    var D = '#chat-settings-dialog';
    return [
      D + ' .MuiPaper-root{background-color:' + c.paperBg + '!important;color:' + c.textColor + '!important}',
      D + ' .MuiTypography-root,' + D + ' .MuiDialogTitle-root,' + D + ' .MuiDialogContent-root{color:' + c.textColor + '!important}',
      D + ' .MuiButton-root{color:' + c.BLUE + '!important;border-color:' + c.BLUE + '!important}',
      D + ' .MuiButton-root:hover{background-color:rgba(69,136,211,0.08)!important}',
      D + ' .MuiSlider-root{color:' + c.BLUE + '!important}',
      D + ' .MuiSlider-rail{background-color:' + c.railBg + '!important;opacity:1!important}',
      D + ' .MuiSlider-track{background-color:' + c.BLUE + '!important;border-color:' + c.BLUE + '!important}',
      D + ' .MuiSlider-thumb{background-color:' + c.BLUE + '!important}',
      D + ' .MuiSlider-valueLabel{background-color:' + c.BLUE + '!important;color:#fff!important}',
      D + ' .MuiOutlinedInput-root{background-color:' + c.inputBg + '!important;color:' + c.textColor + '!important}',
      D + ' .MuiSelect-select{color:' + c.textColor + '!important}',
      D + ' .MuiOutlinedInput-notchedOutline{border-color:rgba(69,136,211,0.5)!important}',
      D + ' .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline{border-color:' + c.BLUE + '!important;border-width:2px!important}',
      D + ' .MuiSelect-icon{color:' + c.mutedColor + '!important}',
      D + ' .MuiInputLabel-root{color:' + c.mutedColor + '!important}',
      D + ' .MuiSwitch-track{background-color:' + c.railBg + '!important;opacity:1!important}',
      D + ' .MuiSwitch-switchBase.Mui-checked{color:' + c.BLUE + '!important}',
      D + ' .MuiSwitch-switchBase.Mui-checked+.MuiSwitch-track{background-color:' + c.BLUE + '!important;opacity:0.5!important}',
    ].join('\n');
  }

  function injectSettingsStyles() {
    var c     = getThemeColors();
    var theme = c.isDark ? 'dark' : 'light';
    var tag   = document.getElementById('ag-settings-override');

    if (tag && _lastInjectedTheme === theme) {
      document.head.appendChild(tag); // keep it last in <head>
      return;
    }
    _lastInjectedTheme = theme;

    if (!tag) {
      tag = document.createElement('style');
      tag.id = 'ag-settings-override';
    }
    tag.textContent = buildSettingsCSS(c);
    document.head.appendChild(tag);
  }

  /* Theme the Select dropdown that MUI portals outside the dialog */
  function fixSelectDropdown() {
    var c = getThemeColors();
    document.querySelectorAll('.MuiPaper-root').forEach(function (paper) {
      var items = paper.querySelectorAll('.MuiMenuItem-root');
      if (!items.length) return;
      // Skip the user-menu (it has its own Switch for dark mode)
      if (paper.querySelector('.MuiSwitch-root')) return;

      paper.style.setProperty('background-color', c.menuBg, 'important');
      paper.style.setProperty('color', c.textColor, 'important');
      paper.querySelectorAll('ul, .MuiList-root').forEach(function (el) {
        el.style.setProperty('background-color', 'transparent', 'important');
      });
      items.forEach(function (item) {
        item.style.setProperty('color', c.textColor, 'important');
        if (item.classList.contains('Mui-selected')) {
          item.style.setProperty('color', c.BLUE, 'important');
          item.style.setProperty('background-color', 'rgba(69,136,211,0.18)', 'important');
        } else {
          item.style.setProperty('background-color', 'transparent', 'important');
        }
      });
    });
  }

  /* Keep our override stylesheet at the end of <head> so Emotion can't outrank it */
  function watchHeadStyles() {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        m.addedNodes.forEach(function (node) {
          if (node.nodeType !== 1 || node.tagName !== 'STYLE') return;
          if (node.id === 'ag-settings-override') return;
          var tag = document.getElementById('ag-settings-override');
          if (tag) document.head.appendChild(tag);
        });
      });
    }).observe(document.head, { childList: true });
  }

  /* Minor tweaks */
  function fixPlaceholder() {
    var ta = document.querySelector('textarea');
    if (ta && ta.placeholder !== "Let's get started...")
      ta.placeholder = "Let's get started...";
  }

  /* Walk up from the textarea and clear any opaque backgrounds */
  function fixChatboxGap() {
    var ta = document.querySelector('textarea');
    if (!ta) return;
    var el = ta.parentElement;
    while (el && el.tagName !== 'MAIN' && el.tagName !== 'BODY') {
      var bg = window.getComputedStyle(el).backgroundColor;
      if (bg && bg !== 'transparent' && bg !== 'rgba(0, 0, 0, 0)') {
        var hasPaper = el.classList.contains('MuiPaper-root');
        if (!hasPaper) {
          el.style.setProperty('background', 'transparent', 'important');
          el.style.setProperty('background-color', 'transparent', 'important');
        }
      }
      el = el.parentElement;
    }
  }

  function runAll() {
    fillEmailField();
    hideSidebarToggle();
    hideCopyButtons();
    injectGithubButton();
    replaceUserAvatar();
    injectTagline();
    fixPlaceholder();
    fixChatboxGap();
    applyThemeBridge();
    injectSettingsStyles();
    fixSelectDropdown();
  }

  var observer = new MutationObserver(runAll);

  function start() {
    runAll();
    observer.observe(document.body, { childList: true, subtree: true });

    // Tick a few extra times during the React hydration window
    var _earlyTicks = 0;
    var _earlyInterval = setInterval(function () {
      runAll();
      _earlyTicks++;
      if (_earlyTicks >= 10) clearInterval(_earlyInterval);
    }, 500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { start(); watchHeadStyles(); });
  } else {
    start();
    watchHeadStyles();
  }
})();
