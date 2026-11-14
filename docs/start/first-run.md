# The first sign-in

The keeper signs everyone in, to itself and to every application it runs. On a
new installation nobody has an account yet; the first person in is the one who
can read a file on the machine.

## 1. Sign in with the access token

On its first start the keeper makes:

- an **access token**, in `~/.rho/auth/master.token`, readable by your user
  only;
- the **signing key pair** every sign-in ticket and service token is signed
  with, in the same folder.

Open <http://127.0.0.1:19090/>. With nobody in the people store, the sign-in
page asks for the access token and nothing else. Print it on the machine and
paste it:

```sh
cat ~/.rho/auth/master.token
```

Five wrong tokens in a row close the sign-in for five minutes.

## 2. Make your account

Signed in with the token, you are the admin but nobody in particular. Open
**Users & access** (`/people`): the page offers **Make your account** — a name,
a display name and a password of at least ten characters. Your session becomes
that account, and you sign in with your name and password from then on.

The access token keeps working. The sign-in page offers it as *The admin's
access token instead*, which is how an admin gets in after forgetting a
password.

## 3. Add the people who sign in

**Users & access → Add a person** takes a name (lowercase letters, digits, `.`,
`_` or `-`), a display name, a role, grants and a first password, which they can
change under **Account**.

| Role | May |
|---|---|
| admin | everything: installing applications, people, plugins, settings |
| operator | start, stop, restart, build and redeploy the applications |
| viewer | read |

The role is about the keeper. What a person reaches **inside** an application is
their grants, written as scopes:

| Grant | Means |
|---|---|
| `mesh:*` | everything in Mesh |
| `mesh:greenhouse` | read and change the mesh called `greenhouse` |
| `mesh:read` | read every mesh |
| `aquarium:read` | a grant for the aquarium |

A sign-in ticket for an application carries the person's name and only their
grants for that application; an admin's carry `*`. Someone with no grant for an
application is told they have no access rather than signed in. Mesh reads the
grant to decide what a person may change ({ref}`mesh/index`); the other
applications let in anyone with a grant for them.

The people store is `~/.rho/keeper/users.yml`, owner-only. Passwords are hashed
by the `rho auth` component; the keeper never puts one on a command line.

## Signing in to the applications

Signed in to the keeper, you are signed in to every application you may use:
opening one sends the browser to the keeper and back with a one-use ticket, and
the application keeps a session of its own. Signing out of the keeper — or
**Sign out everywhere** on a person's row — ends their application sessions at
the next request, within a minute.

## Recovery

| Problem | What to do |
|---|---|
| A person forgot their password | an admin sets a new one on their row in Users & access |
| The admin forgot theirs | sign in with the access token, then set a new password |
| From the command line | `rho auth user passwd --store ~/.rho/keeper/users.yml --name ana --password-file <file>` |
| The access token may have leaked | **Recovery token** in the rail: give the current one and set a new one; every other session is signed out |
| The signing key may have leaked | **Recovery token → Rotate the signing key**; tickets signed with the old key stop working at once |

## Next

{ref}`start/applications` — installing and running the applications.
