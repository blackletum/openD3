/*
===========================================================================

openD3 update signing key
Copyright (C) 2026 DarkMatter Productions

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

===========================================================================
*/

#ifndef __OPEND3_UPDATE_SIGNING_KEY_H__
#define __OPEND3_UPDATE_SIGNING_KEY_H__

// The Ed25519 public key that signs each release's opend3-update.json, as 64
// hex digits. `tools/build/update_manifest.py keygen` writes it here; the
// private half is the OPEND3_UPDATE_SIGNING_KEY secret of the release
// workflow and is never committed.
//
// Empty means this build trusts no manifest signature: the update check still
// reports a newer release, but the game opens the release page instead of
// installing it in place.
// OPEND3: empty. openD3 has no release key yet; the key upstream ships here
// signs openQ4's releases, not openD3's.
#define OPEND3_UPDATE_SIGNING_PUBLIC_KEY ""

#endif /* !__OPEND3_UPDATE_SIGNING_KEY_H__ */
