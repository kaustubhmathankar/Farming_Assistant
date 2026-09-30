import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import AuthPage from "./pages/AuthPage";
import ChatPage from "./pages/ChatPage";
import ProfilePage from "./pages/ProfilePage";
import AdminPage from "./pages/AdminPage";

function StartRoute() { const { isAuthenticated } = useAuth(); return <Navigate to={isAuthenticated ? "/chat" : "/auth"} replace />; }

export default function App() {
  return <Routes><Route path="/" element={<StartRoute />} /><Route path="/auth" element={<AuthPage />} /><Route element={<ProtectedRoute />}><Route element={<AppLayout />}><Route path="/chat" element={<ChatPage />} /><Route path="/profile" element={<ProfilePage />} /></Route></Route><Route element={<ProtectedRoute adminOnly />}><Route element={<AppLayout />}><Route path="/admin" element={<AdminPage />} /></Route></Route><Route path="*" element={<StartRoute />} /></Routes>;
}
