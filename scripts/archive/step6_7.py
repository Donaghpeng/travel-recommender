import sys, os
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Donaghy\Desktop\travel-recommender\static'
path = os.path.join(base, 'js', 'app.js')
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# ── Step 6: Add "查看推荐" button to POI cards ──
# Find the end of each POI card rendering
# The pattern near the card close:
# html += '    </div>';  (closes the flex div)
# html += '  </div>';    (closes the result-card div)
# So we insert after the flex div close, before the card close

# Find this exact block in renderPOIResults:
old_block = "    html += '    </div>';\n    html += '  </div>';\n    html += '</div>';\n  }\n\n  resEl.innerHTML = html;"

# Replace with version that includes the button
new_block = (
    "    html += '    </div>';\n"
    "    // POI → 推荐按钮\n"
    "    if (city) {\n"
    "      html += '  <div style=\"padding:8px 12px;border-top:1px solid var(--border-default)\">';\n"
    "      html += '    <button class=\"poi-to-recommend\" onclick=\"goToRecommendFromPOI(\\'' + escapeHtml(city) + '\\')\" style=\"width:100%;padding:8px;background:var(--accent);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:13px\">';\n"
    "      html += '      \\ud83c\\udfaf \\u67e5\\u770b ' + escapeHtml(city) + ' \\u63a8\\u8350\\u65b9\\u6848';\n"
    "      html += '    </button>';\n"
    "      html += '  </div>';\n"
    "    }\n"
    "    html += '</div>';\n"
    "  }\n\n"
    "  resEl.innerHTML = html;"
)

if old_block not in c:
    print('ERROR: Could not find target block')
    # Try to find alternatives
    idx = c.find("html += '</div>';\n  }\n\n  resEl.innerHTML = html;")
    if idx >= 0:
        print(f'Found partial match at {idx}')
        print(repr(c[idx-100:idx+100]))
    else:
        print('No match at all')
    sys.exit(1)

c = c.replace(old_block, new_block, 1)
print('Step 6: POI button inserted')

# ── Step 7: Add goToRecommendFromPOI function ──
# Find a good insertion point - after the search button handler and before renderResults
fn_def = '\n// ── \u6e32\u67d3\u7ed3\u679c ──'
if fn_def not in c:
    # Try renderResults
    fn_def = '\nfunction renderResults'
    
idx = c.find(fn_def)
if idx >= 0:
    new_fn = (
        '\n\n// ── POI\u8df3\u8f6c\u5230\u63a8\u8350Tab ──\n'
        'function goToRecommendFromPOI(city) {\n'
        '  if (!city) return;\n'
        '  // \u8bbe\u7f6e\u504f\u597d\u6846\n'
        '  var pref = document.getElementById("preferences");\n'
        '  if (pref) {\n'
        '    var old = pref.value;\n'
        '    if (old && old !== city) {\n'
        '      pref.value = city + ", " + old;\n'
        '    } else {\n'
        '      pref.value = city;\n'
        '    }\n'
        '  }\n'
        '  // \u5207\u6362\u5230\u63a8\u8350Tab\n'
        '  switchTab("recommend");\n'
        '  // \u89e6\u53d1\u641c\u7d22\n'
        '  var btn = document.getElementById("searchBtn");\n'
        '  if (btn) btn.click();\n'
        '}'
    )
    c = c[:idx] + new_fn + c[idx:]
    print('Step 7: goToRecommendFromPOI function added')
else:
    print('ERROR: Could not find insertion point for goToRecommendFromPOI')
    sys.exit(1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print(f'Done! File written: {len(c)} bytes')
