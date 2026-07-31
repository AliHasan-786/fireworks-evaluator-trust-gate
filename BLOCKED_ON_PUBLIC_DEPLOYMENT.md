# Public deployment status

The production-ready static artifact is in `public_site/`. This file will be updated after the deployment attempt.

Exact single next action if Vercel authentication is unavailable:

```bash
vercel login && vercel deploy public_site --prod -y
```
