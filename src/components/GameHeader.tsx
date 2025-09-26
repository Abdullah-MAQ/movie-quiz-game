import { Trophy, User, Star } from "lucide-react";
import { GameButton } from "./GameButton";

interface GameHeaderProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function GameHeader({ currentPage, onNavigate }: GameHeaderProps) {
  const navItems = [
    { id: "quiz", label: "Quiz", icon: Star },
    { id: "leaderboard", label: "Leaderboard", icon: Trophy },
    { id: "profile", label: "Profile", icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 bg-gradient-gaming backdrop-blur-lg border-b border-border/50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
              <Star className="w-6 h-6 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              CineQuiz
            </h1>
          </div>
          
          <nav className="hidden md:flex space-x-2">
            {navItems.map(({ id, label, icon: Icon }) => (
              <GameButton
                key={id}
                variant={currentPage === id ? "primary" : "secondary"}
                size="sm"
                onClick={() => onNavigate(id)}
                className="flex items-center space-x-2"
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </GameButton>
            ))}
          </nav>

          <GameButton
            variant="warning"
            size="sm"
            onClick={() => onNavigate("login")}
          >
            Logout
          </GameButton>
        </div>
      </div>
    </header>
  );
}