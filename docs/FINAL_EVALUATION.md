# OnboardAI: Final Review Evaluation

Generated 05 November 2026, 11:33 by `python -m evaluation.report`.

Every case below was written by hand after the models were trained, in wording that does not come from the training data generators. The same cases run live in the app under **HR login > Evaluation Lab**.

## Summary

| What was tested | Cases | Result |
| --- | --- | --- |
| Chatbot routing: intent of a hand-written message | 48 | 72.9% correct (93.7% on the synthetic test set) |
| Chatbot sentiment | 48 | 66.7% correct |
| Policy search: right section ranked first | 12 | 83.3% (top 3: 91.7%) |
| Policy search: finds nothing when the handbook has no answer | 2 | 2 of 2 |
| Policy search: never shows another company's handbook | 2 | 2 of 2 |
| Full assistant answers: correct fact with citation, or honest decline | 16 | 75.0%, mean 32.1s per reply (qwen2.5:7b) |
| Full answers: correct fact (handbook covers it) | 12 | 11 of 12 |
| Full answers: cites the handbook section | 12 | 9 of 12 |
| Full answers: declines when it should (no answer, or other company only) | 4 | 3 of 4 |
| Document verification: correct verdict | 16 | 100.0% |
| Document verification: bad documents wrongly approved | 16 | 0 |

## Main finding

The intent classifier scores 93.7% on held-out synthetic messages but 72.9% on messages written naturally by a person. The model learned the templates' vocabulary, so unfamiliar phrasing costs accuracy. The system tolerates this because every specialist agent can hand a conversation to the right one, and low-confidence messages go to the general Onboarding Agent instead of being forced into a specialist. The fix for the next version is training on real or more varied messages, not more of the same templates.

## 1. Chatbot routing

| Intent | Correct |
| --- | --- |
| document help | 5 / 6 |
| it access | 6 / 6 |
| kt schedule | 6 / 6 |
| policy question | 4 / 6 |
| status check | 4 / 6 |
| payroll benefits | 3 / 6 |
| escalation | 3 / 6 |
| smalltalk | 4 / 6 |

Misses:

| Message | Expected | Predicted | Confidence |
| --- | --- | --- | --- |
| I sent the bank form yesterday and it still hasn't been checked, really annoying | document_help | it_access | 32.4% |
| Can I work from Goa for a couple of weeks? | policy_question | document_help | 59.6% |
| What safety gear is compulsory on the factory floor? | policy_question | status_check | 42.1% |
| Am I nearly done with all the joining formalities? | status_check | payroll_benefits | 22.1% |
| Just finished my training, so what's next for me? | status_check | kt_schedule | 28.8% |
| On what date does salary get credited each month? | payroll_benefits | policy_question | 53.0% |
| I want to change the bank account my pay goes into | payroll_benefits | it_access | 55.6% |
| When will my PF account be opened? | payroll_benefits | it_access | 97.9% |
| Please get me a real person, the bot isn't helping | escalation | it_access | 47.3% |
| Honestly I'm thinking of withdrawing my acceptance, this is chaos | escalation | it_access | 23.7% |
| I want to raise a formal complaint about how my onboarding has been handled | escalation | status_check | 71.9% |
| Hey there! | smalltalk | policy_question | 33.2% |
| Have a nice weekend | smalltalk | it_access | 73.8% |

## 2. Policy search

| Question | Asked by | Expected | Top result | Result |
| --- | --- | --- | --- | --- |
| How many days of annual leave do I get each year? | Nimbus Labs | org_1__leave_policy / Annual leave | Leave Policy (Nimbus Labs) / Annual leave (0.625) | pass |
| How many days of annual leave do I get each year? | Veltrix Corp | org_2__leave_policy / Annual leave | Leave Policy (Veltrix Corp) / Annual leave (0.6) | pass |
| Do I need a doctor's note if I'm off sick? | Nimbus Labs | org_1__leave_policy / Sick leave | Leave Policy (Nimbus Labs) / Sick leave (0.625) | pass |
| Can I work from another country for a while? | Nimbus Labs | org_1__remote_work / Working from abroad | Remote Work Policy (Nimbus Labs) / Remote Work Policy - Nimbus Labs (0.512) | FAIL |
| How much will the company pay towards a desk and chair at home? | Nimbus Labs | org_1__remote_work / Equipment at home | Remote Work Policy (Nimbus Labs) / Equipment at home (0.675) | pass |
| What's the deadline for submitting an expense claim? | Nimbus Labs | shared__equipment_and_expenses / Expense claims | Equipment and Expenses / Expense claims (0.782) | pass |
| Who do I tell if I think customer data has been breached? | Nimbus Labs | org_1__information_security / Incidents | Information Security (Nimbus Labs) / Customer data (0.678) | FAIL |
| Can I take leave while I'm on probation? | Nimbus Labs | org_1__leave_policy / Leave during probation | Leave Policy (Nimbus Labs) / Leave during probation (0.627) | pass |
| Can I accept a gift from a supplier? | Nimbus Labs | shared__code_of_conduct / Gifts | Code of Conduct / Gifts (0.651) | pass |
| What extra pay do I get for working nights? | Veltrix Corp | org_2__shift_patterns / Shift allowance | Shift Patterns (Veltrix Corp) / Shift allowance (0.446) | pass |
| What protective gear do I need on the production floor? | Veltrix Corp | org_2__safety_policy / Personal protective equipment | Plant Safety Policy (Veltrix Corp) / Personal protective equipment (0.593) | pass |
| How long is a safety certificate valid for? | Veltrix Corp | org_2__safety_policy / Certification | Plant Safety Policy (Veltrix Corp) / Certification (0.695) | pass |
| Is there a gym membership or wellness allowance? | Nimbus Labs | decline | nothing | pass |
| What is the company's stock option vesting schedule? | Nimbus Labs | decline | nothing | pass |
| What is the lockout-tagout procedure for machine maintenance? | Nimbus Labs | nothing from org_2 | Information Security (Nimbus Labs) / Customer data (0.14) | pass |
| Am I allowed to work from abroad, and for how long? | Veltrix Corp | nothing from org_1 | Plant Safety Policy (Veltrix Corp) / Lockout-tagout (0.174) | pass |

## 3. Full assistant answers

**P01 (pass, 27.2s, Policy Agent)**: How many days of annual leave do I get each year? *(Nimbus Labs)*

> According to the Leave Policy (Nimbus Labs) — Annual leave, you receive 24 days of paid annual leave per calendar year, accrued monthly at 2 days per month. Up to 10 unused days may be carried into the following year. 
> 
> Is there anything else related to leave you'd like to know, or do you have any other questions about your onboarding?

**P02 (pass, 18.0s, Policy Agent)**: How many days of annual leave do I get each year? *(Veltrix Corp)*

> According to the Leave Policy (Veltrix Corp) — Annual leave, you are entitled to 18 days of paid annual leave per calendar year. It's important to request leave at least two weeks in advance so that shift cover can be arranged. 
> 
> Is there anything else you need help with regarding your leave entitlements?

**P03 (pass, 44.8s, Policy Agent)**: Do I need a doctor's note if I'm off sick? *(Nimbus Labs)*

> According to the Leave Policy (Nimbus Labs) — Sick leave, you need a medical certificate (which can be a doctor's note) for any absence of more than three consecutive working days. For shorter absences, you can use your sick leave without a note. If you have any further questions, feel free to ask!

**P04 (pass, 38.4s, Policy Agent)**: Can I work from another country for a while? *(Nimbus Labs)*

> According to our Remote Work Policy, working from abroad requires written approval from both your manager and People Operations, and is limited to 30 days per year due to tax reasons.
> 
> Would you like me to help you raise a request for this with your manager and HR?

**P05 (pass, 37.1s, Policy Agent)**: How much will the company pay towards a desk and chair at home? *(Nimbus Labs)*

> According to our Remote Work Policy (Nimbus Labs) — Equipment at home, the company contributes up to INR 15,000 towards a desk and chair, and this contribution is claimable once every three years. 
> 
> Is there anything else related to your setup or any other questions you have?

**P06 (pass, 31.1s, Policy Agent)**: What's the deadline for submitting an expense claim? *(Nimbus Labs)*

> According to the company policy, expense claims must be submitted within 30 days of the expense being incurred, and they are reimbursed with the following month's salary. If you have any further questions or need assistance, feel free to ask!

**P07 (FAIL, 48.6s, Policy Agent)**: Who do I tell if I think customer data has been breached? *(Nimbus Labs)*

> According to our company policies, if you think customer data has been breached, you should report it to the Information Security team. You can reach out to them directly for guidance.
> 
> If you need immediate assistance, you can contact the Information Security team at [infosec@nimbuslabs.com](mailto:infosec@nimbuslabs.com) or call them at [123-456-7890](tel:123-456-7890).
> 
> Thank you for bringing this to our attention, and I'm here to support you through this process.

**P08 (pass, 24.1s, Policy Agent)**: Can I take leave while I'm on probation? *(Nimbus Labs)*

> According to the Leave Policy (Nimbus Labs), you can take leave during your probation period, but it is limited to 6 days in total and requires manager approval in advance. For sick leave, you have 12 days of paid sick leave per year, and for annual leave, you receive 24 days per calendar year, accrued monthly at 2 days per month, with up to 10 unused days carried into the following year.
> 
> If you need to take leave, please ensure you discuss it with your manager to get the necessary approval.

**P09 (pass, 36.0s, Policy Agent)**: Can I accept a gift from a supplier? *(Nimbus Labs)*

> According to the Code of Conduct at Nimbus Labs, gifts with a value above INR 2,000 must be declared to your manager. Cash gifts may never be accepted. It's important to adhere to these guidelines to maintain professionalism and avoid conflicts of interest.
> 
> If you have any more questions or need further clarification, feel free to ask!

**P10 (pass, 16.8s, Policy Agent)**: What extra pay do I get for working nights? *(Veltrix Corp)*

> For working nights, you will receive a 25% allowance on your basic pay. This information can be found in the Shift Patterns document under the section on shift allowance. If you have any further questions or need more details, feel free to ask!

**P11 (FAIL, 50.7s, Policy Agent)**: What protective gear do I need on the production floor? *(Veltrix Corp)*

> On the production floor, you will need to wear steel-toed boots, high-visibility vests, and eye protection at all times. Additionally, hearing protection is required in the press shop. It's also important to ensure that your safety certification is current, as it must be renewed every three years. If you have any questions or need further assistance, feel free to ask!

**P12 (FAIL, 43.0s, Policy Agent)**: How long is a safety certificate valid for? *(Veltrix Corp)*

> At Veltrix Corp, a safety certificate is valid for three years. It must be renewed before it expires to ensure you can continue entering the production floor safely.

**P13 (pass, 15.2s, Policy Agent)**: Is there a gym membership or wellness allowance? *(Nimbus Labs)*

> Hi Shreya,
> 
> I've checked our company policies and found no specific mention of a gym membership or wellness allowance. I can raise this with HR on your behalf if you'd like. Would you like to proceed with that?
> 
> Best,
> [Your Name]

**P14 (pass, 18.4s, Policy Agent)**: What is the company's stock option vesting schedule? *(Nimbus Labs)*

> Hi Shreya,
> 
> I've checked our company policies, but there's no specific document covering the stock option vesting schedule. I understand this might be causing some uncertainty. Would you like to discuss this further with HR to ensure we have the most accurate information for you?
> 
> Best,
> [Your Name]

**P15 (FAIL, 43.0s, IT Provisioning Agent)**: What is the lockout-tagout procedure for machine maintenance? *(Nimbus Labs)*

> Hi Shreya,
> 
> Thank you for reaching out. I understand that the lockout-tagout procedure for machine maintenance is outside my remit as an IT Provisioning Agent. This procedure is typically managed by our Safety and Compliance team. Would you like me to transfer you to the appropriate specialist who can provide you with the details you need?
> 
> Best,
> [Your Name]

**P16 (pass, 21.2s, Policy Agent)**: Am I allowed to work from abroad, and for how long? *(Veltrix Corp)*

> I'm sorry, but I don't have a specific policy document that addresses working from abroad or the duration of such work. According to the documents I have, there is no clear guidance on this topic. 
> 
> For your safety and compliance, I recommend speaking with HR to discuss any plans to work from abroad. They can provide you with the necessary information and ensure that all procedures are followed.
> 
> Would you like me to raise this with HR on your behalf?

## 4. Document verification

| Document | Uploaded as | Expected | Given | Reason |
| --- | --- | --- | --- | --- |
| Signed offer letter | Offer Letter Signed | auto_approved | auto_approved | All automated checks passed. |
| Offer letter, never signed | Offer Letter Signed | auto_rejected | auto_rejected | This document type must be signed, but no signature was detected. |
| Offer letter, signature line left blank | Offer Letter Signed | needs_review | needs_review | A signature field was found but it appears to be empty; HR should confirm it is signed. |
| Valid passport | Govt ID / Passport | auto_approved | auto_approved | All automated checks passed. |
| Somebody else's passport | Govt ID / Passport | needs_review | needs_review | Could not confirm the document belongs to Shreya Nair (names found: MEHTA, RAHUL). |
| Expired passport | Govt ID / Passport | auto_rejected | auto_rejected | Document expired on 2026-09-16 (50 days ago). |
| Valid safety certificate | Safety Certification | auto_approved | auto_approved | All automated checks passed. |
| Expired safety certificate | Safety Certification | auto_rejected | auto_rejected | Document expired on 2026-04-19 (200 days ago). |
| Safety certificate expiring in 10 days | Safety Certification | needs_review | needs_review | Document expires on 2026-11-15, in 10 days. |
| Cafeteria memo uploaded as bank form | Direct Deposit Form | auto_rejected | auto_rejected | This does not look like any onboarding document, but 'Direct Deposit Form' was requested. |
| Passport uploaded as offer letter | Offer Letter Signed | auto_rejected | auto_rejected | This looks like a govt id, but 'Offer Letter Signed' was requested. |
| Signed salary account form | Direct Deposit Form | auto_approved | auto_approved | All automated checks passed. |
| Salary account form, unsigned | Direct Deposit Form | auto_rejected | auto_rejected | This document type must be signed, but no signature was detected. |
| Signed background check consent | Background Check Consent | auto_approved | auto_approved | All automated checks passed. |
| Phone-quality scan of a signed offer letter | Offer Letter Signed | auto_approved | auto_approved | All automated checks passed. |
| Photo of a document (no OCR engine on server) | Govt ID / Passport | needs_review | needs_review | This looks like a scan or photo and no OCR engine is installed on the server, so HR will review it manually. |

The files are in `backend/demo_documents/final_review/` and can be uploaded by hand.
