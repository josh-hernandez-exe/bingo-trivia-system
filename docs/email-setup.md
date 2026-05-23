# Email setup

## Microsoft Graph (delegated)

1. In the Azure portal → **App registrations** → **New registration**.
2. Account type: "Single tenant" is fine.
3. After creation, copy the **Tenant ID** and **Application (client) ID** into
   your `.env`:

   ```bash
   GRAPH_TENANT_ID=...
   GRAPH_CLIENT_ID=...
   ```

4. Under **API permissions** add **Delegated → Microsoft Graph → Mail.Send**.
   Grant admin consent if your tenant requires it.
5. Under **Authentication** → **Advanced settings** → enable **Allow public
   client flows** (this is what makes device-code auth work).
6. First `bts send --transport graph` triggers a device-code login; the token
   is cached in `~/.cache/bts/graph-token.json`.

Emails come from your own mailbox, so replies work as expected.

## AWS SES

1. In the SES console for your region, verify the **From** identity (either
   the full address or its domain).
2. Request **production access** if you're outside the SES sandbox.
3. Set environment variables:

   ```bash
   AWS_PROFILE=default        # or whichever profile has SES permissions
   AWS_REGION=us-east-1
   SES_FROM_ADDR=trivia@yourdomain.com
   ```

4. `bts send --transport ses` does the rest.

## Cross-transport sanity check

Before event day, send a test to yourself via both transports and compare:

```bash
bts send --transport graph --only you@yourdomain.com
bts send --transport ses   --only you@yourdomain.com
```

Both emails should render identically and contain the same PDF attachments.
