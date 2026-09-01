# Testing Report-Mistake Submission Flow

## Overview
This document provides comprehensive testing instructions for the report-mistake feature fix (PR #19).

## What Was Fixed
- ✅ API now validates honeypot fields and required data
- ✅ API returns proper error responses with status codes
- ✅ Client shows actual error messages when submission fails
- ✅ Added 30-second rate limiting between submissions
- ✅ Success screen only shows when API confirms receipt
- ✅ Added spam protection via honeypot field

## Prerequisites
For actual email delivery, set these environment variables in Vercel:
- `RESEND_API_KEY` (required) - Your Resend API key
- `REPORT_TO_EMAIL` (optional, defaults to kobykarp@gmail.com)
- `REPORT_FROM_EMAIL` (optional, defaults to Watch With The Kids <onboarding@resend.dev>)

## Test Cases

### Test 1: Successful Submission (Episode Page)
**Location:** Any episode page (e.g., `/ep/friends/0101.html`)

1. Click "Report mistake" button at bottom of page
2. Modal should open with episode title (e.g., "S1 E1 · The One Where...")
3. Select a reason (e.g., "Wrong score (V / S / L)")
4. Optionally add details in textarea
5. Click "Send report"
6. Button should show "Sending..." and be disabled
7. **Expected:** Success screen with checkmark and "Thanks — noted." message
8. Click "Done" to close

**Validation:**
- If `RESEND_API_KEY` is set: Email should arrive at `REPORT_TO_EMAIL`
- Report stored in localStorage under key `wwtk-reports` (check browser DevTools > Application > Local Storage)
- Check browser Network tab: POST to `/api/report` should return 200 OK

### Test 2: Successful Submission (Show Page)
**Location:** Any show page (e.g., `/friends.html`)

1. Find any episode card in the list
2. Click "Report mistake" button in card footer
3. Follow steps 3-8 from Test 1

### Test 3: Error Handling - Missing API Key
**Setup:** Remove `RESEND_API_KEY` from environment

1. Follow Test 1 steps 1-5
2. **Expected:** Error message: "Email service not configured. Report saved locally."
3. Submit button should be re-enabled
4. User can try again or cancel

**Validation:**
- API returns 500 status
- Error message is visible in red text above buttons
- Report still saved to localStorage

### Test 4: Rate Limiting
1. Submit a report successfully (follow Test 1)
2. Click "Done" to close success screen
3. Immediately open report modal again
4. Select a reason and try to submit
5. **Expected:** Error message: "Please wait 30 seconds between reports."
6. Submit button stays disabled
7. Wait 30+ seconds and try again
8. **Expected:** Submission works normally

**Validation:**
- Check localStorage key `wwtk-report-last` (timestamp in milliseconds)
- Time difference between submissions must be ≥30000ms

### Test 5: Honeypot Spam Protection
**Setup:** Manually fill the hidden honeypot field via browser DevTools

1. Open report modal
2. Open DevTools Console
3. Run: `document.querySelector('input[name="website"]').value = 'spam'`
4. Select a reason and click "Send report"
5. **Expected:** Error message: "Spam detected."
6. No network request sent (check Network tab)

**Validation:**
- Client-side validation prevents submission
- No POST request to `/api/report`
- Error shown immediately

### Test 6: Network Error Handling
**Setup:** Simulate network failure (e.g., offline mode or block `/api/report` in DevTools)

1. Open DevTools > Network tab
2. Right-click `/api` folder and "Block request domain" or enable offline mode
3. Try to submit a report
4. **Expected:** Error message: "Failed to send. Please try again."
5. Submit button re-enabled
6. User can retry

### Test 7: Server Error Handling
**Setup:** API returns error (e.g., invalid JSON or 500 error)

1. Temporarily modify `/api/report.js` to always return an error, OR
2. Send invalid payload (missing required field)
3. Try to submit a report
4. **Expected:** Error message with server error description
5. Submit button re-enabled

### Test 8: Modal Interactions
1. Open report modal
2. Click outside modal (on backdrop) → should close
3. Open modal again
4. Press `Escape` key → should close
5. Open modal again
6. Click X button in top right → should close
7. Open modal again
8. Click "Cancel" button → should close

### Test 9: Required Field Validation
1. Open report modal
2. Try to click "Send report" without selecting a reason
3. **Expected:** Button stays disabled (grayed out)
4. Select a reason
5. **Expected:** Button becomes enabled
6. Can now submit

### Test 10: Details Field (Optional)
1. Open report modal
2. Select a reason
3. Leave details field empty and submit
4. **Expected:** Submission succeeds (details are optional)
5. Try again with details filled in
6. **Expected:** Submission succeeds and details included

## Manual Inspection

### Code Locations
- **Client-side:** `web/episode.js` (lines ~167-244), `web/show.js` (lines ~955-1033)
- **API:** `web/api/report.js`
- **CSS:** `web/friends.css` (lines 1322-1720, report-* classes)

### Key Changes
```javascript
// Honeypot check (both episode.js and show.js)
const honeypot = form.querySelector('input[name="website"]');
if (honeypot && honeypot.value) {
  errEl.textContent = "Spam detected.";
  errEl.hidden = false;
  return;
}

// Rate limiting check
const rateLimitKey = "wwtk-report-last";
const now = Date.now();
const last = Number(localStorage.getItem(rateLimitKey) || "0");
if (last && now - last < 30000) {
  errEl.textContent = "Please wait 30 seconds between reports.";
  errEl.hidden = false;
  return;
}

// Response validation
if (!res.ok) {
  const data = await res.json().catch(() => ({ error: "Failed to send" }));
  throw new Error(data.error || `Server error: ${res.status}`);
}
```

### API Changes
```javascript
// Honeypot validation
if (body.website || body.url || body.homepage) {
  return res.status(400).json({ error: "Invalid submission" });
}

// Required fields
if (!body.reason || !body.show) {
  return res.status(400).json({ error: "Missing required fields" });
}

// Email delivery validation
if (!emailSent && !key) {
  return res.status(500).json({ 
    error: "Email service not configured. Report saved locally." 
  });
}
```

## Browser DevTools Inspection

### Check localStorage
```javascript
// In browser console:
localStorage.getItem('wwtk-reports')      // All reports queue
localStorage.getItem('wwtk-report-last')  // Last submission timestamp
```

### Check Network Tab
1. Filter: `/api/report`
2. Request should show:
   - Method: POST
   - Status: 200 (success) or 500 (error)
   - Payload: JSON with show, reason, details, etc.
3. Response should show:
   - Success: `{"ok": true}`
   - Error: `{"error": "message here"}`

### Check Console
- Look for `[report]` prefixed logs
- Errors will show with full stack trace

## Production Testing (After Deployment)

1. Visit https://watchwiththekids.com/friends.html
2. Test any of the above scenarios
3. Verify actual email delivery at configured address
4. Check Vercel function logs:
   - Go to Vercel dashboard
   - Select project
   - Go to "Functions" tab
   - Find `/api/report` function
   - Check logs for `[report]` entries

## Expected Behavior Summary

| Scenario | Expected Result |
|----------|----------------|
| Valid submission with API key | ✅ Success screen, email sent, report logged |
| Valid submission without API key | ❌ Error shown, report saved locally only |
| Honeypot filled | ❌ "Spam detected" error, no request sent |
| Rate limited | ❌ "Wait 30 seconds" error, no request sent |
| Network error | ❌ "Failed to send" error, button re-enabled |
| Server error | ❌ Server error message shown, button re-enabled |
| No reason selected | Submit button disabled |
| Missing details | ✅ Success (details optional) |

## Notes
- All reports are saved to localStorage as backup, even if API fails
- Only last 80 reports kept in localStorage (circular buffer)
- Rate limit stored per browser (not account-based)
- Honeypot field is hidden with CSS (`position:absolute;left:-9999px`)
- Error messages are styled in red (`.report-error` class)
