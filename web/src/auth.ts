const TOKEN_KEY = 'mindpalace_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(username: string, password: string): Promise<string> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error('Invalid credentials');
  const data = await res.json();
  setToken(data.token);
  return data.token;
}

export async function register(username: string, password: string, displayName?: string): Promise<string> {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, display_name: displayName || username }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(err.detail || 'Registration failed');
  }
  const data = await res.json();
  setToken(data.token);
  return data.token;
}

export async function checkAuth(): Promise<boolean> {
  const token = getToken();
  if (!token) return false;
  try {
    const res = await fetch('/api/auth/check', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ── WebAuthn / Passkeys ────────────────────────────

function bufferToBase64Url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlToBuffer(base64url: string): ArrayBuffer {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

export async function getPasskeyStatus(): Promise<{ registered: boolean; count: number }> {
  const res = await fetch('/api/auth/webauthn/status', { headers: authHeaders() });
  if (!res.ok) return { registered: false, count: 0 };
  return res.json();
}

export async function registerPasskey(): Promise<void> {
  // 1. Get registration options from server
  const beginRes = await fetch('/api/auth/webauthn/register/begin', {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!beginRes.ok) throw new Error('Failed to start registration');
  const options = await beginRes.json();

  // 2. Decode challenge and user.id
  options.challenge = base64UrlToBuffer(options.challenge);
  options.user.id = base64UrlToBuffer(options.user.id);
  if (options.excludeCredentials) {
    options.excludeCredentials = options.excludeCredentials.map((c: { id: string; type: string }) => ({
      ...c,
      id: base64UrlToBuffer(c.id),
    }));
  }

  // 3. Create credential (triggers biometric prompt)
  const credential = (await navigator.credentials.create({ publicKey: options })) as PublicKeyCredential;
  if (!credential) throw new Error('Credential creation cancelled');

  const attestation = credential.response as AuthenticatorAttestationResponse;

  // 4. Send to server
  const completeRes = await fetch('/api/auth/webauthn/register/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({
      credential: {
        id: credential.id,
        rawId: bufferToBase64Url(credential.rawId),
        response: {
          attestationObject: bufferToBase64Url(attestation.attestationObject),
          clientDataJSON: bufferToBase64Url(attestation.clientDataJSON),
        },
        type: credential.type,
      },
    }),
  });
  if (!completeRes.ok) throw new Error('Registration failed');
}

export async function loginWithPasskey(): Promise<string> {
  // 1. Get authentication options
  const beginRes = await fetch('/api/auth/webauthn/login/begin', { method: 'POST' });
  if (!beginRes.ok) throw new Error('No passkeys registered');
  const options = await beginRes.json();

  // 2. Decode challenge and allowCredentials
  options.challenge = base64UrlToBuffer(options.challenge);
  if (options.allowCredentials) {
    options.allowCredentials = options.allowCredentials.map((c: { id: string; type: string }) => ({
      ...c,
      id: base64UrlToBuffer(c.id),
    }));
  }

  // 3. Get credential (triggers biometric prompt)
  const credential = (await navigator.credentials.get({ publicKey: options })) as PublicKeyCredential;
  if (!credential) throw new Error('Authentication cancelled');

  const assertion = credential.response as AuthenticatorAssertionResponse;

  // 4. Send to server
  const completeRes = await fetch('/api/auth/webauthn/login/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      credential: {
        id: credential.id,
        rawId: bufferToBase64Url(credential.rawId),
        response: {
          authenticatorData: bufferToBase64Url(assertion.authenticatorData),
          clientDataJSON: bufferToBase64Url(assertion.clientDataJSON),
          signature: bufferToBase64Url(assertion.signature),
          userHandle: assertion.userHandle ? bufferToBase64Url(assertion.userHandle) : null,
        },
        type: credential.type,
      },
    }),
  });
  if (!completeRes.ok) throw new Error('Biometric auth failed');
  const data = await completeRes.json();
  setToken(data.token);
  return data.token;
}
