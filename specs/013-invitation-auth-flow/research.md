# Research: Invitation-Only User Authentication

## Decision 1: Keep invitation signup custom, use Django built-in password reset

- Decision: Preserve the custom invitation accept flow in `sitesync` and implement password reset with Django's tokenized auth views and custom templates.
- Rationale: The codebase already owns invitation acceptance as a domain-specific flow, while the password-reset stub should be upgraded to a standard secure lifecycle instead of inventing a new token system.
- Alternatives considered: Rewriting invitation signup as a built-in auth flow, or hand-rolling a password-reset token service. Both add complexity without improving the feature.

## Decision 2: Use branded email templates rendered through Anymail/Mailtrap

- Decision: Keep Anymail/Mailtrap as the delivery layer and move invitation/reset content into reusable branded text/HTML templates.
- Rationale: The settings already switch to Mailtrap when configured, and template-backed messages keep the brand consistent while making the content easier to test and evolve.
- Alternatives considered: Inline plain-text email bodies in views, or a separate outbound-mail service with no template reuse. Both would duplicate logic and make branding harder to maintain.

## Decision 3: Implement logout confirmation as a shared modal

- Decision: Use a reusable modal partial plus a small client-side handler, wired into the shared topbar/admin shell layouts.
- Rationale: The current app already has mixed server-rendered layouts, so a modal fits both the public pages and the admin panel without introducing a new UI framework.
- Alternatives considered: A dedicated logout confirmation page, or a full-page redirect flow. Those are explicit but less seamless for the current layout system.

## Decision 4: Add a feature-specific contract document

- Decision: Document the auth flow in a dedicated contract file under the feature folder.
- Rationale: The feature exposes user-facing routes, invitation actions, and email-template variables that deserve a narrow contract for implementation and verification.
- Alternatives considered: Reusing the older generic user-management contract. That would be too broad for the new invitation-only auth behavior.

## Decision 5: Model invitation revocation explicitly

- Decision: Treat revoked invitations as a first-class state and keep the invite link invalid once revoked.
- Rationale: The spec already requires a clear invalid-link response for revoked invites, and the admin UI needs an explicit control path for that state.
- Alternatives considered: Overloading expired or accepted states to mean revoked. That would blur intent and make tests harder to read.