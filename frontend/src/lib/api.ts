export type BoardPayload = {
  columns: Array<{ id: string; title: string; cardIds: string[] }>;
  cards: Record<string, { id: string; title: string; details: string }>;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const getAuthToken = () => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem("kanban-access-token");
};

export const login = async (username: string, password: string) => {
  const response = await fetch(`${API_BASE_URL}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("Invalid username or password.");
  }

  const data = await response.json();
  return data.access_token as string;
};

export const fetchBoard = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(`${API_BASE_URL}/api/board`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error("Unable to load board.");
  }

  return (await response.json()) as BoardPayload;
};

export const saveBoard = async (board: BoardPayload) => {
  const token = getAuthToken();
  if (!token) {
    return board;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/board`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(board),
    });

    if (!response.ok) {
      return board;
    }

    return (await response.json()) as BoardPayload;
  } catch {
    return board;
  }
};
