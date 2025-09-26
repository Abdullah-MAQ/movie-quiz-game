import { useState, useEffect } from "react";
import { LoginPage } from "@/components/LoginPage";
import { GameHeader } from "@/components/GameHeader";
import { QuizPage } from "@/components/QuizPage";
import { LeaderboardPage } from "@/components/LeaderboardPage";
import { ProfilePage } from "@/components/ProfilePage";

interface UserData {
  user_id: string;
  email: string;
  preferred_genre: string;
}

const Index = () => {
  const [currentPage, setCurrentPage] = useState<string>("login");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState<UserData | null>(null);

  useEffect(() => {
    // Check if user is already logged in
    const storedUserData = localStorage.getItem("userData");
    if (storedUserData) {
      try {
        const parsedData = JSON.parse(storedUserData);
        setUserData(parsedData);
        setIsLoggedIn(true);
        setCurrentPage("quiz");
      } catch (error) {
        localStorage.removeItem("userData");
      }
    }
  }, []);

  const handleLogin = (loginUserData: UserData) => {
    setUserData(loginUserData);
    setIsLoggedIn(true);
    setCurrentPage("quiz");
  };

  const handleNavigation = (page: string) => {
    if (page === "login") {
      setIsLoggedIn(false);
      setUserData(null);
      setCurrentPage("login");
      localStorage.removeItem("userData");
    } else {
      setCurrentPage(page);
    }
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const renderPage = () => {
    switch (currentPage) {
      case "quiz":
        return <QuizPage userData={userData} onNavigate={handleNavigation} />;
      case "leaderboard":
        return <LeaderboardPage userData={userData} />;
      case "profile":
        return <ProfilePage userData={userData} />;
      default:
        return <QuizPage userData={userData} onNavigate={handleNavigation} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-gaming">
      <GameHeader currentPage={currentPage} onNavigate={handleNavigation} />
      {renderPage()}
    </div>
  );
};

export default Index;