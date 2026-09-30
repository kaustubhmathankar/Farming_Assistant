const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api/v1";

const TOKEN_KEY =
  "krishisaathi_token";


export function getToken() {
  return localStorage.getItem(
    TOKEN_KEY
  );
}


export function setToken(token) {
  localStorage.setItem(
    TOKEN_KEY,
    token
  );
}


export function clearToken() {
  localStorage.removeItem(
    TOKEN_KEY
  );
}


async function request(
  path,
  options = {}
) {
  const headers = new Headers(
    options.headers || {}
  );

  const token = getToken();

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  if (
    !(options.body instanceof FormData) &&
    !headers.has(
      "Content-Type"
    )
  ) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  const response = await fetch(
    `${BASE_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  const data =
    await response
      .json()
      .catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data?.detail ||
        data?.message ||
        "Request failed"
    );

    error.status =
      response.status;

    throw error;
  }

  return data;
}


async function fetchImageBlobUrl(
  path
) {
  const token = getToken();

  const headers =
    new Headers();

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    `${BASE_URL}${path}`,
    {
      method: "GET",
      headers,
    }
  );

  if (!response.ok) {
    const data =
      await response
        .json()
        .catch(() => ({}));

    const error = new Error(
      data?.detail ||
        "Unable to load image"
    );

    error.status =
      response.status;

    throw error;
  }

  const blob =
    await response.blob();

  return URL.createObjectURL(
    blob
  );
}


export const api = {
  register: (body) =>
    request(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(
          body
        ),
      }
    ),

  login: (body) =>
    request(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify(
          body
        ),
      }
    ),

  me: () =>
    request("/auth/me"),

  logout: () =>
    request(
      "/auth/logout",
      {
        method: "POST",
      }
    ),

  changePassword: (body) =>
    request(
      "/auth/change-password",
      {
        method: "POST",
        body: JSON.stringify(
          body
        ),
      }
    ),

  profile: () =>
    request(
      "/farmers/me"
    ),

  updateProfile: (body) =>
    request(
      "/farmers/me",
      {
        method: "PUT",
        body: JSON.stringify(
          body
        ),
      }
    ),

  conversations: () =>
    request(
      "/conversations"
    ),

  conversation: (id) =>
    request(
      `/conversations/${id}`
    ),

  imageBlobUrl: (path) =>
    fetchImageBlobUrl(path),

  deleteConversation: (id) =>
    request(
      `/conversations/${id}`,
      {
        method: "DELETE",
      }
    ),

  chat: (body) =>
    request(
      "/agent/chat",
      {
        method: "POST",
        body: JSON.stringify(
          body
        ),
      }
    ),

  imageChat: (form) =>
    request(
      "/agent/image-chat",
      {
        method: "POST",
        body: form,
      }
    ),

  voiceChat: (form) =>
    request(
      "/agent/voice-chat",
      {
        method: "POST",
        body: form,
      }
    ),

  adminDashboard: () =>
    request(
      "/admin/dashboard"
    ),

  adminUsers: () =>
    request(
      "/admin/users"
    ),

  updateAdminUser: (
    id,
    body
  ) =>
    request(
      `/admin/users/${id}`,
      {
        method: "PATCH",
        body: JSON.stringify(
          body
        ),
      }
    ),
};