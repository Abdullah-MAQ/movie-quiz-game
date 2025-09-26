import { useState } from "react";
import { Eye, EyeOff, User, Lock, Mail } from "lucide-react";
import { GameButton } from "./GameButton";
import { GameCard } from "./GameCard";
import { GameHeader } from "./GameHeader";
import { API_CONFIG } from "@/lib/config";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Film, Star, Trophy, Zap } from "lucide-react";

interface LoginPageProps {
  onLogin: (userData: any) => void;
}

const MOVIE_GENRES = [
  "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Drama",
  "Family", "Fantasy", "Film-Noir", "History", "Horror", "Music", "Musical",
  "Mystery", "Romance", "Sci-Fi", "Sport", "Thriller", "War", "Western"
];

export function LoginPage({ onLogin }: LoginPageProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [preferredGenre, setPreferredGenre] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
      const payload: any = { email, password };
      
      if (!isLogin) {
        if (!preferredGenre) {
          setError("Please select your preferred movie genre");
          setIsLoading(false);
          return;
        }
        payload.preferred_genre = preferredGenre;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        // Store user data in localStorage
        localStorage.setItem("userData", JSON.stringify(data));
        onLogin(data);
      } else {
        setError(data.error || "Authentication failed");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-gaming flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid md:grid-cols-2 gap-8 items-center">
        {/* Hero Section */}
        <div className="text-center md:text-left space-y-6">
          <div className="flex items-center justify-center md:justify-start space-x-3">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center animate-pulse-glow">
              <Film className="w-8 h-8 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-4xl md:text-6xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                CineQuiz
              </h1>
              <p className="text-accent text-lg">Movie Trivia Championship</p>
            </div>
          </div>
          
          <p className="text-xl text-muted-foreground max-w-md">
            Test your movie knowledge, compete with friends, and climb the leaderboard in the ultimate cinema challenge!
          </p>

          <div className="grid grid-cols-3 gap-4 max-w-md">
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-secondary rounded-lg mx-auto flex items-center justify-center mb-2">
                <Star className="w-6 h-6 text-secondary-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">AI-Powered Questions</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-success rounded-lg mx-auto flex items-center justify-center mb-2">
                <Trophy className="w-6 h-6 text-success-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">Global Leaderboard</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-primary rounded-lg mx-auto flex items-center justify-center mb-2">
                <Zap className="w-6 h-6 text-primary-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">Real-time Scoring</p>
            </div>
          </div>
        </div>

        {/* Login Form */}
        <GameCard variant="glow" className="p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-foreground mb-2">
                {isLogin ? "Welcome Back!" : "Join the Game"}
              </h2>
              <p className="text-muted-foreground">
                {isLogin ? "Ready to test your movie knowledge?" : "Create your account and start playing"}
              </p>
            </div>

            {error && (
              <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <Label htmlFor="email" className="text-foreground">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-muted/50 border-border/50 focus:border-primary"
                  placeholder="your@email.com"
                  required
                  disabled={isLoading}
                />
              </div>
              
              <div>
                <Label htmlFor="password" className="text-foreground">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-muted/50 border-border/50 focus:border-primary"
                  placeholder="••••••••"
                  required
                  disabled={isLoading}
                />
              </div>

              {!isLogin && (
                <div>
                  <Label htmlFor="genre" className="text-foreground">Preferred Movie Genre</Label>
                  <Select value={preferredGenre} onValueChange={setPreferredGenre} disabled={isLoading}>
                    <SelectTrigger className="bg-muted/50 border-border/50 focus:border-primary">
                      <SelectValue placeholder="Choose your favorite genre" />
                    </SelectTrigger>
                    <SelectContent>
                      {MOVIE_GENRES.map((genre) => (
                        <SelectItem key={genre} value={genre}>
                          {genre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground mt-1">
                    This will help us customize quiz questions for you!
                  </p>
                </div>
              )}
            </div>

            <GameButton
              variant="primary"
              size="lg"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? "Please wait..." : (isLogin ? "Start Playing" : "Create Account")}
            </GameButton>

            <div className="text-center">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-accent hover:text-accent/80 transition-colors"
              >
                {isLogin ? "New player? Create account" : "Already have an account? Login"}
              </button>
            </div>
          </form>
        </GameCard>
      </div>
    </div>
  );
}