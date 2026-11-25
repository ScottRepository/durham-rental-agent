// Content script injected on demand to auto-fill visible inputs on Facebook, Kijiji, Zumper, or Rentals.ca
window.__kentStAutoFill = function(payload, platform) {
  function setNativeValue(el, value) {
    if (!el || value === undefined || value === null) return false;
    el.focus();
    const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) {
      setter.call(el, String(value));
    } else {
      el.value = String(value);
    }
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
    return true;
  }

  function findVisible(selectors) {
    for (const sel of selectors) {
      const els = document.querySelectorAll(sel);
      for (const el of els) {
        if (el.offsetParent !== null && !el.disabled && el.type !== 'hidden') {
          return el;
        }
      }
    }
    return null;
  }

  let filledCount = 0;
  const cleanPrice = String(payload.price || '').replace(/[^0-9]/g, '');
  const videoUrl = payload.virtual_tour_url || payload.youtube_video_url || payload.video_link || '';

  if (platform === 'facebook') {
    // Facebook Marketplace labels wrap inputs/textareas
    const labels = Array.from(document.querySelectorAll('label'));
    for (const lbl of labels) {
      const txt = (lbl.innerText || '').toLowerCase();
      const inp = lbl.querySelector('input, textarea');
      if (!inp || inp.offsetParent === null) continue;
      if (txt.includes('bedrooms') && setNativeValue(inp, payload.bedrooms)) filledCount++;
      else if (txt.includes('bathrooms') && setNativeValue(inp, payload.bathrooms)) filledCount++;
      else if (txt.includes('price') && setNativeValue(inp, cleanPrice)) filledCount++;
      else if (txt.includes('square feet') && setNativeValue(inp, payload.sqft || '800')) filledCount++;
      else if (txt.includes('description') && setNativeValue(inp, payload.description)) filledCount++;
      else if (txt.includes('address') && setNativeValue(inp, '315 Kent Street, Whitby, ON')) filledCount++;
    }
  } else if (platform === 'kijiji') {
    if (setNativeValue(findVisible(["#AdTitleForm", "input[name*='title']"]), payload.title)) filledCount++;
    if (setNativeValue(findVisible(["#pstad-descrptn", "textarea[name*='description']"]), payload.description)) filledCount++;
    if (setNativeValue(findVisible(["#PriceAmount", "input[name*='priceAmount']"]), cleanPrice)) filledCount++;
    if (videoUrl && setNativeValue(findVisible(["input[name*='youtube' i]", "input[id*='youtube' i]"]), videoUrl)) filledCount++;
    if (setNativeValue(findVisible(["input#pstad-loc-txt", "input[placeholder*='Postal code']"]), "315 Kent Street, Whitby, ON")) filledCount++;
  } else {
    // Zumper & Rentals.ca multi-step wizards (fills whichever fields are visible on the current step!)
    if (setNativeValue(findVisible(["input[placeholder*='address' i]", "input[name*='address' i]"]), "315 Kent Street, Whitby, ON")) filledCount++;
    const unitNum = (payload.unit_id || 'unit_3').replace('unit_', '');
    if (setNativeValue(findVisible(["input[placeholder*='unit' i]", "input[name*='unit' i]", "input[placeholder*='apt' i]"]), `Unit ${unitNum}`)) filledCount++;
    if (setNativeValue(findVisible(["input[name*='bed' i]"]), payload.bedrooms)) filledCount++;
    if (setNativeValue(findVisible(["input[name*='bath' i]"]), payload.bathrooms)) filledCount++;
    if (setNativeValue(findVisible(["input[name*='sqft' i]", "input[placeholder*='sq' i]"]), payload.sqft || '800')) filledCount++;
    if (setNativeValue(findVisible(["input[name*='rent' i]", "input[placeholder*='rent' i]", "input[name*='price' i]"]), cleanPrice)) filledCount++;
    if (setNativeValue(findVisible(["textarea"]), payload.description)) filledCount++;
    if (videoUrl && setNativeValue(findVisible(["input[placeholder*='youtube' i]", "input[placeholder*='video' i]", "input[type='url']"]), videoUrl)) filledCount++;
  }

  return filledCount;
};
