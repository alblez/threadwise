"""HTML email body fixtures for testing the email processor."""

SIMPLE_HTML = """\
<html>
<body>
<p>Hi team,</p>
<p>Please review the <a href="https://example.com/doc">design document</a> before our meeting.</p>
<p>The <b>deadline</b> is Friday.</p>
</body>
</html>"""

OUTLOOK_HTML = """\
<html xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:w="urn:schemas-microsoft-com:office:word">
<head>
<!--[if gte mso 9]><xml><o:OfficeDocumentSettings>
<o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]-->
<style>
.MsoNormal { margin: 0in; font-size: 11pt; font-family: "Calibri",sans-serif; }
</style>
</head>
<body>
<div class="WordSection1">
<p class="MsoNormal"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif">
Hi everyone,</span></p>
<p class="MsoNormal"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif">
I wanted to share the quarterly results. Revenue is up 15% compared to last quarter.</span></p>
<p class="MsoNormal"><span style="font-size:11.0pt;font-family:&quot;Calibri&quot;,sans-serif">
Let me know if you have questions.</span></p>
</div>
</body>
</html>"""

GMAIL_REPLY_HTML = """\
<html>
<body>
<div dir="ltr">
<p>Thanks for the update. I agree with the proposed timeline.</p>
</div>
<div class="gmail_quote">
<div class="gmail_attr">On Mon, Jan 15, 2024 at 10:00 AM
Alice &lt;alice@example.com&gt; wrote:</div>
<blockquote class="gmail_quote"
style="margin:0px 0px 0px 0.8ex;border-left:1px solid rgb(204,204,204);
padding-left:1ex">
<div dir="ltr">
<p>Here is the project timeline for Q1. Please review and let me know your thoughts.</p>
</div>
</blockquote>
</div>
</body>
</html>"""

HTML_WITH_SIGNATURE = """\
<html>
<body>
<p>The deployment is scheduled for next Tuesday at 3pm EST.</p>
<p>Please make sure all PRs are merged by Monday EOD.</p>
<p>--</p>
<p>Jane Doe<br/>
Senior Engineer, Platform Team<br/>
Phone: +1-555-0199<br/>
<a href="https://acme.com">acme.com</a></p>
</body>
</html>"""

HTML_WITH_TRACKING = """\
<html>
<body>
<p>Meeting notes from today's standup are attached.</p>
<p>Action items have been assigned in Jira.</p>
<img src="https://track.sendgrid.net/wf/open/abc123" width="1" height="1" />
<div style="display:none">
<p>You are receiving this email because you are subscribed to updates.</p>
</div>
</body>
</html>"""

PLAIN_TEXT_WITH_SIGNATURE = """\
Hey, just checking in on the status of the API migration.

Are we still on track for the March release?

Sent from my iPhone"""

HTML_WITH_REGARDS_SIGNATURE = """\
<html>
<body>
<p>I've reviewed the contract and everything looks good from our side.</p>
<p>We can proceed with signing next week.</p>
<p>Best regards,</p>
<p>John Smith<br/>
CTO, Acme Corp<br/>
+1-555-0123<br/>
www.acme.com</p>
</body>
</html>"""
