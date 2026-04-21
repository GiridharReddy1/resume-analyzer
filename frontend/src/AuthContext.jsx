import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("resumeiq_user");
    if (stored) setUser(JSON.parse(stored));
  }, []);

  const signup = (name, email, password) => {
    const users = JSON.parse(localStorage.getItem("resumeiq_users") || "[]");
    if (users.find((u) => u.email === email))
      return { success: false, error: "Email already registered." };
    users.push({ name, email, password });
    localStorage.setItem("resumeiq_users", JSON.stringify(users));
    const session = { name, email };
    localStorage.setItem("resumeiq_user", JSON.stringify(session));
    setUser(session);
    return { success: true };
  };

  const login = (email, password) => {
    const users = JSON.parse(localStorage.getItem("resumeiq_users") || "[]");
    const match = users.find((u) => u.email === email && u.password === password);
    if (!match) return { success: false, error: "Invalid email or password." };
    const session = { name: match.name, email: match.email };
    localStorage.setItem("resumeiq_user", JSON.stringify(session));
    setUser(session);
    return { success: true };
  };

  const logout = () => {
    localStorage.removeItem("resumeiq_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

