# robohub-auth

The SSO plugin an application names to use Keeper as its authorization server.

```yaml
plugins:
  - name: robohub-auth
    enabled: true
```

The application's `project.yml` carries the request middleware and its public
deployment shape:

```yaml
middleware:
  - name: auth
    options:
      issuer: keeper
      audience: aquarium
      cookie: aquarium_session
      public_key: /home/me/.rho/auth/public.pem
      mode: proxy
      public_url: https://example.com
      base_path: /aquarium
      login_url: https://auth.example.com/auth/login
```

For a direct WAN address, omit `public_url`/`base_path` and set
`mode: direct`, `login_url: http://<address>:19090/auth/login`.
