import os

css_addition = """
/* ==========================================================================
   Google DevSite Modern Code Block & Callout Styling Extension
   ========================================================================== */

.codelab-code-wrapper {
  position: relative;
  margin: 1.6em 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(60, 64, 67, 0.12), 0 1px 2px rgba(60, 64, 67, 0.08);
  transition: all 0.2s ease;
}

.codelab-code-wrapper.theme-dark {
  background-color: #202124 !important;
  border: 1px solid #3c4043;
}

.codelab-code-wrapper.theme-light {
  background-color: #f8f9fa !important;
  border: 1px solid #dadce0;
}

.codelab-code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  user-select: none;
  font-size: 12px;
}

.codelab-code-wrapper.theme-dark .codelab-code-header {
  background-color: #282a2e;
  border-bottom: 1px solid #3c4043;
  color: #9aa0a6;
}

.codelab-code-wrapper.theme-light .codelab-code-header {
  background-color: #edf2f7;
  border-bottom: 1px solid #e2e8f0;
  color: #5f6368;
}

.codelab-code-lang {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.codelab-code-lang::before {
  content: "";
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #1a73e8;
}

.codelab-code-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.codelab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 5px;
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.15s ease-in-out;
  background: transparent;
  outline: none;
}

.codelab-code-wrapper.theme-dark .codelab-btn {
  color: #e8eaed;
  background-color: rgba(255, 255, 255, 0.05);
}
.codelab-code-wrapper.theme-dark .codelab-btn:hover {
  background-color: #3c4043;
  border-color: #5f6368;
}

.codelab-code-wrapper.theme-light .codelab-btn {
  color: #3c4043;
  background-color: rgba(0, 0, 0, 0.04);
}
.codelab-code-wrapper.theme-light .codelab-btn:hover {
  background-color: #e2e8f0;
  border-color: #cbd5e1;
}

.codelab-code-wrapper pre {
  margin: 0 !important;
  padding: 16px 18px !important;
  border-radius: 0 !important;
  border: none !important;
  overflow-x: auto;
  font-family: "Roboto Mono", Consolas, "Fira Code", monospace !important;
  font-size: 13.5px !important;
  line-height: 1.65 !important;
}

.codelab-code-wrapper.theme-dark pre,
.codelab-code-wrapper.theme-dark pre code {
  background-color: #202124 !important;
  color: #f1f3f4 !important;
}

.codelab-code-wrapper.theme-light pre,
.codelab-code-wrapper.theme-light pre code {
  background-color: #f8f9fa !important;
  color: #202124 !important;
}

/* Syntax highlighting in Dark mode */
.codelab-code-wrapper.theme-dark .kwd { color: #78d9ec !important; font-weight: 600; }
.codelab-code-wrapper.theme-dark .str { color: #9ccc65 !important; }
.codelab-code-wrapper.theme-dark .com { color: #9aa0a6 !important; font-style: italic; }
.codelab-code-wrapper.theme-dark .lit { color: #fbbc04 !important; }
.codelab-code-wrapper.theme-dark .typ { color: #d7aefb !important; }
.codelab-code-wrapper.theme-dark .pun,
.codelab-code-wrapper.theme-dark .opn,
.codelab-code-wrapper.theme-dark .clo { color: #cfd8dc !important; }
.codelab-code-wrapper.theme-dark .pln { color: #f1f3f4 !important; }

/* Syntax highlighting in Light mode */
.codelab-code-wrapper.theme-light .kwd { color: #1967d2 !important; font-weight: 600; }
.codelab-code-wrapper.theme-light .str { color: #188038 !important; }
.codelab-code-wrapper.theme-light .com { color: #5f6368 !important; font-style: italic; }
.codelab-code-wrapper.theme-light .lit { color: #b06000 !important; }
.codelab-code-wrapper.theme-light .typ { color: #7b1fa2 !important; }
.codelab-code-wrapper.theme-light .pun,
.codelab-code-wrapper.theme-light .opn,
.codelab-code-wrapper.theme-light .clo { color: #3c4043 !important; }
.codelab-code-wrapper.theme-light .pln { color: #202124 !important; }

/* Callout Styling (區塊有底色) */
.codelab-callout {
  position: relative;
  margin: 1.8em 0;
  padding: 16px 22px 16px 56px;
  border-radius: 8px;
  font-size: 14.5px;
  line-height: 1.65;
  box-shadow: 0 1px 3px rgba(60, 64, 67, 0.08);
}

.codelab-callout .callout-icon {
  position: absolute;
  top: 16px;
  left: 18px;
  font-size: 22px;
  line-height: 1;
}

.codelab-callout-header {
  font-weight: 700;
  font-size: 15px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.codelab-callout-positive {
  background-color: #e6f4ea;
  border-left: 5px solid #137333;
  color: #137333;
}
.codelab-callout-positive .callout-body {
  color: #202124;
}
.codelab-callout-positive code {
  background-color: rgba(19, 115, 51, 0.12) !important;
  color: #137333 !important;
  padding: 2px 6px;
  border-radius: 4px;
}

.codelab-callout-negative {
  background-color: #fef7e0;
  border-left: 5px solid #f9ab00;
  color: #b06000;
}
.codelab-callout-negative .callout-body {
  color: #202124;
}
.codelab-callout-negative code {
  background-color: rgba(176, 96, 0, 0.12) !important;
  color: #b06000 !important;
  padding: 2px 6px;
  border-radius: 4px;
}

.codelab-callout-info {
  background-color: #e8f0fe;
  border-left: 5px solid #1a73e8;
  color: #1a73e8;
}
.codelab-callout-info .callout-body {
  color: #202124;
}
.codelab-callout-info code {
  background-color: rgba(26, 115, 232, 0.12) !important;
  color: #1a73e8 !important;
  padding: 2px 6px;
  border-radius: 4px;
.codelab-callout a {
  color: #1a73e8 !important;
  text-decoration: underline !important;
  font-weight: 600 !important;
}
.codelab-callout a:hover {
  color: #1557b0 !important;
}
.codelab-callout a code {
  color: #1a73e8 !important;
  background-color: rgba(26, 115, 232, 0.12) !important;
  text-decoration: underline !important;
}

/* Also style native blockquotes */
google-codelab-step blockquote {
  margin: 1.8em 0;
  padding: 14px 20px 14px 50px;
  background-color: #f1f3f4;
  border-left: 4px solid #1a73e8;
  border-radius: 8px;
  position: relative;
  font-style: normal;
  color: #3c4043;
}
google-codelab-step blockquote::before {
  content: "💡";
  position: absolute;
  top: 14px;
  left: 16px;
  font-size: 20px;
}
"""

js_addition = """
/* ==========================================================================
   Google DevSite Modern Code Block & Callout JavaScript Extension
   ========================================================================== */

(function() {
  const STORAGE_KEY = 'codelab_code_theme_pref';
  let currentTheme = localStorage.getItem(STORAGE_KEY) || 'dark';

  function getIcon(name) {
    if (name === 'sun') {
      return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
    }
    if (name === 'moon') {
      return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
    }
    if (name === 'copy') {
      return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
    }
    if (name === 'check') {
      return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    }
    return '';
  }

  function detectLanguage(codeEl, text) {
    if (codeEl) {
      for (const cls of codeEl.classList) {
        if (cls.startsWith('language-') || cls.startsWith('lang-')) {
          return cls.replace('language-', '').replace('lang-', '').toUpperCase();
        }
      }
      if (codeEl.getAttribute('language')) {
        return codeEl.getAttribute('language').replace('language-', '').toUpperCase();
      }
    }
    const trimmed = text.trim();
    if (trimmed.includes('sudo ') || trimmed.includes('apt-get') || trimmed.includes('brew ') || trimmed.includes('winget ') || trimmed.includes('docker ') || trimmed.includes('curl ') || trimmed.includes('k6 run') || trimmed.startsWith('$') || trimmed.startsWith('PS>')) {
      return 'BASH';
    }
    if (trimmed.includes('import ') || trimmed.includes('export default') || trimmed.includes('export const') || trimmed.includes('function(') || trimmed.includes('const res =')) {
      return 'JAVASCRIPT';
    }
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      return 'JSON';
    }
    if (trimmed.includes('version:') || trimmed.includes('services:') || trimmed.includes('image:')) {
      return 'YAML';
    }
    return 'CODE';
  }

  function enhanceCodeBlocks() {
    const pres = document.querySelectorAll('google-codelab-step pre:not([data-enhanced])');
    pres.forEach((pre) => {
      pre.setAttribute('data-enhanced', 'true');
      
      const wrapper = document.createElement('div');
      wrapper.className = `codelab-code-wrapper theme-${currentTheme}`;
      
      const codeEl = pre.querySelector('code');
      const rawText = codeEl ? codeEl.innerText : pre.innerText;
      const lang = detectLanguage(codeEl, rawText);

      // Create Header
      const header = document.createElement('div');
      header.className = 'codelab-code-header';
      header.innerHTML = `
        <span class="codelab-code-lang">${lang}</span>
        <div class="codelab-code-actions">
          <button type="button" class="codelab-btn codelab-theme-toggle" title="切換代碼區塊深色/淺色主題">
            ${getIcon(currentTheme === 'dark' ? 'sun' : 'moon')}
            <span class="btn-text">${currentTheme === 'dark' ? '淺色' : '深色'}</span>
          </button>
          <button type="button" class="codelab-btn codelab-copy-btn" title="複製代碼">
            ${getIcon('copy')}
            <span class="btn-text">複製</span>
          </button>
        </div>
      `;

      // Copy Action
      const copyBtn = header.querySelector('.codelab-copy-btn');
      copyBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        try {
          await navigator.clipboard.writeText(rawText);
          copyBtn.innerHTML = `${getIcon('check')} <span class="btn-text" style="color:#10b981;font-weight:bold;">已複製！</span>`;
          setTimeout(() => {
            copyBtn.innerHTML = `${getIcon('copy')} <span class="btn-text">複製</span>`;
          }, 2000);
        } catch (err) {
          const ta = document.createElement('textarea');
          ta.value = rawText;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          copyBtn.innerHTML = `${getIcon('check')} <span class="btn-text" style="color:#10b981;font-weight:bold;">已複製！</span>`;
          setTimeout(() => {
            copyBtn.innerHTML = `${getIcon('copy')} <span class="btn-text">複製</span>`;
          }, 2000);
        }
      });

      // Theme Toggle Action
      const themeToggle = header.querySelector('.codelab-theme-toggle');
      themeToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, currentTheme);
        document.querySelectorAll('.codelab-code-wrapper').forEach((w) => {
          w.classList.remove('theme-dark', 'theme-light');
          w.classList.add(`theme-${currentTheme}`);
          const toggle = w.querySelector('.codelab-theme-toggle');
          if (toggle) {
            toggle.innerHTML = `${getIcon(currentTheme === 'dark' ? 'sun' : 'moon')} <span class="btn-text">${currentTheme === 'dark' ? '淺色' : '深色'}</span>`;
          }
        });
      });

      // Insert wrapper into DOM
      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(header);
      wrapper.appendChild(pre);
    });
  }

  function enhanceCallouts() {
    const ps = document.querySelectorAll('google-codelab-step p:not([data-enhanced])');
    ps.forEach((p) => {
      const html = p.innerHTML.trim();
      if (html.startsWith('Positive :') || html.startsWith('Positive:')) {
        p.setAttribute('data-enhanced', 'true');
        const content = html.replace(/^Positive\s*:\s*/, '');
        const callout = document.createElement('div');
        callout.className = 'codelab-callout codelab-callout-positive';
        callout.innerHTML = `
          <div class="callout-icon">💡</div>
          <div class="codelab-callout-header">最佳實踐 / 提示 (Best Practice)</div>
          <div class="callout-body">${content}</div>
        `;
        p.parentNode.replaceChild(callout, p);
      } else if (html.startsWith('Negative :') || html.startsWith('Negative:')) {
        p.setAttribute('data-enhanced', 'true');
        const content = html.replace(/^Negative\s*:\s*/, '');
        const callout = document.createElement('div');
        callout.className = 'codelab-callout codelab-callout-negative';
        callout.innerHTML = `
          <div class="callout-icon">⚠️</div>
          <div class="codelab-callout-header">避坑提醒 / 警示 (Warning)</div>
          <div class="callout-body">${content}</div>
        `;
        p.parentNode.replaceChild(callout, p);
      }
    });

    const asides = document.querySelectorAll('google-codelab-step aside:not([data-enhanced])');
    asides.forEach((aside) => {
      aside.setAttribute('data-enhanced', 'true');
      const isWarning = aside.classList.contains('warning');
      aside.className = `codelab-callout ${isWarning ? 'codelab-callout-negative' : 'codelab-callout-positive'}`;
      const inner = aside.innerHTML;
      aside.innerHTML = `
        <div class="callout-icon">${isWarning ? '⚠️' : '💡'}</div>
        <div class="codelab-callout-header">${isWarning ? '避坑提醒 / 警示 (Warning)' : '最佳實踐 / 提示 (Best Practice)'}</div>
        <div class="callout-body">${inner}</div>
      `;
    });
  }

  function getHomeUrl() {
    const codelab = document.querySelector('google-codelab');
    const explicitHome = codelab && (codelab.getAttribute('home-url') || codelab.getAttribute('homeurl'));
    if (explicitHome) return explicitHome;
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    if (pathParts.length > 0 && pathParts[pathParts.length - 1].endsWith('.html')) {
      pathParts.pop();
    }
    if (pathParts.length > 0) {
      pathParts.pop();
    }
    return '/' + (pathParts.length ? pathParts.join('/') + '/' : '');
  }

  function fixBackLink() {
    const homeUrl = getHomeUrl();
    const arrowBack = document.querySelector('#codelab-nav-buttons #arrow-back');
    if (arrowBack) {
      const currentHref = arrowBack.getAttribute('href');
      if (!currentHref || currentHref === '/' || currentHref === '#' || currentHref === '') {
        arrowBack.setAttribute('href', homeUrl);
      }
      if (!arrowBack.getAttribute('data-home-fixed')) {
        arrowBack.setAttribute('data-home-fixed', 'true');
        arrowBack.addEventListener('click', (e) => {
          const href = arrowBack.getAttribute('href');
          if (!href || href === '/') {
            e.preventDefault();
            window.location.href = homeUrl;
          }
        });
      }
    }
    const doneBtn = document.querySelector('#controls #done');
    if (doneBtn) {
      const currentHref = doneBtn.getAttribute('href');
      if (!currentHref || currentHref === '/' || currentHref === '#' || currentHref === '') {
        doneBtn.setAttribute('href', homeUrl);
      }
    }
  }

  function injectBranding() {
    const codelab = document.querySelector('google-codelab');
    if (!codelab) return;
    const codelabId = codelab.getAttribute('id');
    if (codelabId === 'k6-performance-testing') {
      const h1 = document.querySelector('#codelab-title h1.title, #codelab-title .title');
      if (h1 && !h1.getAttribute('data-branded')) {
        h1.setAttribute('data-branded', 'true');
        const icon = document.createElement('img');
        icon.src = '../assets/images/k6-icon-square.png';
        icon.alt = 'k6';
        icon.style.cssText = 'width: 26px; height: 26px; vertical-align: -5px; margin-right: 10px; border-radius: 6px; box-shadow: 0 2px 6px rgba(249,115,22,0.4); display: inline-block;';
        h1.insertBefore(icon, h1.firstChild);
      }
    }
  }

  function init() {
    fixBackLink();
    injectBranding();
    enhanceCodeBlocks();
    enhanceCallouts();

    const observer = new MutationObserver(() => {
      fixBackLink();
      injectBranding();
      enhanceCodeBlocks();
      enhanceCallouts();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['selected', 'animating']
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
"""

script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)

targets = [
    (os.path.join(repo_root, "codelabs/claat-public/codelab-elements.css"), css_addition, "Google DevSite Modern Code Block"),
    (os.path.join(repo_root, "codelabs/generated/claat-public/codelab-elements.css"), css_addition, "Google DevSite Modern Code Block"),
    (os.path.join(repo_root, "codelabs/claat-public/codelab-elements.js"), js_addition, "Google DevSite Modern Code Block"),
    (os.path.join(repo_root, "codelabs/generated/claat-public/codelab-elements.js"), js_addition, "Google DevSite Modern Code Block")
]

for file_path, addition, marker in targets:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if marker in content:
            idx = content.find(marker)
            comment_start = content.rfind("/*", 0, idx)
            if comment_start != -1:
                content = content[:comment_start].rstrip()
            else:
                content = content[:idx].rstrip()

        if file_path.endswith(".js"):
            # Ensure $c() in base codelab-elements.js dynamically resolves home url instead of hardcoded "/"
            if "function $c()" in content:
                idx_start = content.find("function $c()")
                idx_z = content.find("function Z(a,b,c){", idx_start)
                if idx_start != -1 and idx_z != -1:
                    patched_fn = (
                        'function $c(elem){var el=elem||document.querySelector("google-codelab");'
                        'var home=el&&(el.getAttribute("home-url")||el.getAttribute("homeurl"));'
                        'if(home)return home;'
                        'var loc=document.location;'
                        'var a=(new URL(loc.toString())).searchParams.get("index");'
                        'if(a){a=a.replace(/[^a-z0-9\\-]+/ig,"");if(a&&""!==a.trim()){"index"===a&&(a="");return(new URL(a,loc.origin)).pathname}}'
                        'var p=(new URL(loc.toString())).pathname.split("/").filter(Boolean);'
                        'if(p.length>0&&p[p.length-1].endsWith(".html"))p.pop();'
                        'if(p.length>0)p.pop();'
                        'return"/"+(p.length?p.join("/")+"/":"")}'
                    )
                    content = content[:idx_start] + patched_fn + content[idx_z:]
            content = content.replace('Lc(a,sc,{ga:$c()});', 'Lc(a,sc,{ga:$c(a)});')

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content + "\n\n" + addition)
        print(f"Updated extension in {file_path}")
