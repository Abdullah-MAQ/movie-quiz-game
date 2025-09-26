import os
import re
import random
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from semantic_kernel import Kernel
try:
    from semantic_kernel.contents import ChatHistory  # Older style
except Exception:  # pragma: no cover
    try:
        from semantic_kernel.contents.chat_history import ChatHistory  # Newer style
    except Exception:
        ChatHistory = None  # type: ignore
from typing import TYPE_CHECKING

# Attempt to import Google connector; if unavailable we'll fall back.
try:  # pragma: no cover - optional dependency
    from semantic_kernel.connectors.ai.google.google_ai import (
        GoogleAIChatCompletion,
        GoogleAIChatPromptExecutionSettings,
    )  # type: ignore
except Exception:  # pragma: no cover
    GoogleAIChatCompletion = None  # type: ignore
    GoogleAIChatPromptExecutionSettings = None  # type: ignore

try:  # OpenAI fallback
    from semantic_kernel.connectors.ai.open_ai import (
        OpenAIChatCompletion,
        OpenAIChatPromptExecutionSettings,
    )  # type: ignore
except Exception:  # pragma: no cover
    OpenAIChatCompletion = None  # type: ignore
    OpenAIChatPromptExecutionSettings = None  # type: ignore


class QuizGenerator:
    """Encapsulates Semantic Kernel based quiz question generation with adaptive difficulty."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = self._load_dataset(csv_path)
        self.kernel: Optional[Kernel] = None
        self.chat_service: Optional[GoogleAIChatCompletion] = None
        self.execution_settings: Optional[GoogleAIChatPromptExecutionSettings] = None
        self._maybe_init_kernel()

    def _load_dataset(self, path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(path).fillna("")
            df.columns = (
                df.columns
                .str.strip()
                .str.replace('"', "")
                .str.replace("\n", "")
            )
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to load dataset {path}: {e}")

    def _maybe_init_kernel(self):
        # Prefer Google if available, else OpenAI, else fallback mode.
        google_key = os.getenv("GOOGLE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        print(f"[QuizGenerator] Checking API keys...")
        print(f"[QuizGenerator] Google API Key: {'Available' if google_key else 'Not found'}")
        print(f"[QuizGenerator] OpenAI API Key: {'Available' if openai_key else 'Not found'}")
        
        if GoogleAIChatCompletion and google_key:
            try:
                self.chat_service = GoogleAIChatCompletion(
                    gemini_model_id="gemini-1.5-flash",
                    api_key=google_key,
                )
                self.kernel = Kernel()
                self.kernel.add_service(self.chat_service)
                self.execution_settings = GoogleAIChatPromptExecutionSettings(
                    max_output_tokens=1000,  # Increased for better responses
                    temperature=0.3,  # Lower temperature for more consistent output
                )
                print("[QuizGenerator] ✅ Google Gemini API initialized successfully")
            except Exception as e:
                print(f"[QuizGenerator] ❌ Failed to initialize Google API: {e}")
                self.chat_service = None
                self.kernel = None
                self.execution_settings = None
        elif OpenAIChatCompletion and openai_key:
            try:
                self.chat_service = OpenAIChatCompletion(
                    ai_model_id="gpt-4o-mini",
                    api_key=openai_key,
                )
                self.kernel = Kernel()
                self.kernel.add_service(self.chat_service)
                self.execution_settings = OpenAIChatPromptExecutionSettings(
                    max_tokens=800,  # Increased for better responses
                    temperature=0.3,  # Lower temperature for consistency
                )
                print("[QuizGenerator] ✅ OpenAI API initialized successfully")
            except Exception as e:
                print(f"[QuizGenerator] ❌ Failed to initialize OpenAI API: {e}")
                self.chat_service = None
                self.kernel = None
                self.execution_settings = None
        else:
            print("[QuizGenerator] ⚠️ No API keys found, using fallback generation")
            # Fallback: no external service.
            return

    def _select_movie_row(self, difficulty_level: int, preferred_genre: str = None) -> pd.Series:
        # Simple heuristic: use ranking column if present else random.
        df = self.df
        
        # Filter by genre if specified
        if preferred_genre:
            genre_filtered_df = df[df['genre'].str.contains(preferred_genre, case=False, na=False)]
            if not genre_filtered_df.empty:
                df = genre_filtered_df
        
        # Attempt to parse ranking integer from first column name.
        ranking_col = None
        for col in df.columns:
            if "ranking" in col.lower():
                ranking_col = col
                break
        if ranking_col is None:
            return df.sample(1).iloc[0]
        # Partition dataset into buckets for difficulties.
        try:
            df_sorted = df.copy()
            df_sorted["_rank"] = pd.to_numeric(df_sorted[ranking_col], errors="coerce")
            if difficulty_level == 1:
                bucket = df_sorted[df_sorted["_rank"] <= 50]
            elif difficulty_level == 2:
                bucket = df_sorted[(df_sorted["_rank"] > 50) & (df_sorted["_rank"] <= 150)]
            else:
                bucket = df_sorted[df_sorted["_rank"] > 150]
            if bucket.empty:
                bucket = df_sorted
            return bucket.sample(1).iloc[0]
        except Exception:
            return df.sample(1).iloc[0]

    def _build_prompt(self, movie: pd.Series, difficulty_level: int, history: List[Dict[str, Any]]) -> str:
        difficulty_map = {1: "easy", 2: "medium", 3: "hard"}
        difficulty_word = difficulty_map.get(difficulty_level, "medium")
        performance_summary = self._summarize_history(history)
        
        # Clean and prepare movie data
        movie_name = str(movie.get('movie name', '')).strip()
        year = str(movie.get('Year', '')).replace('-', '')
        genre = str(movie.get('genre', '')).strip()
        director = str(movie.get('DIRECTOR', '')).strip()
        plot = str(movie.get('DETAIL ABOUT MOVIE', '')).strip()
        rating = str(movie.get('RATING', '')).strip()
        metascore = str(movie.get('metascore', '')).strip()
        certificate = str(movie.get('certificate', '')).strip()
        runtime = str(movie.get('runtime', '')).strip()
        actor1 = str(movie.get('ACTOR 1', '')).strip()
        actor2 = str(movie.get('ACTOR 2', '')).strip()
        actor3 = str(movie.get('ACTOR 3', '')).strip()
        actor4 = str(movie.get('ACTOR 4', '')).strip()
        
        # Get genre-specific focus areas
        primary_genre = genre.split(',')[0].strip() if genre else "Drama"
        genre_focus = self._get_genre_focus_areas(primary_genre)
        
        template = f"""
You are an expert movie quiz generator specializing in {primary_genre.upper()} films. Create ONE creative {difficulty_word} multiple-choice question about the {primary_genre} movie below.

🎯 PRIORITIZE {primary_genre.upper()}-SPECIFIC QUESTIONS!

For {primary_genre} movies, focus on:
{genre_focus}

You can also ask about:
- {primary_genre}-typical plot elements and themes
- Characteristic {primary_genre} cinematography/techniques  
- Iconic {primary_genre} movie comparisons
- {primary_genre} genre conventions and tropes
- Cast known for {primary_genre} roles
- Directors famous in the {primary_genre} genre

Movie Information:
Title: {movie_name}
Year: {year}
Genre: {genre} (PRIMARY: {primary_genre})
Director: {director}
Main Cast: {actor1}, {actor2}, {actor3}, {actor4}
Plot: {plot}
Rating: {rating}/10  |  Metascore: {metascore}
Certificate: {certificate}  |  Runtime: {runtime}

User Performance: {performance_summary}

Difficulty Guidelines for {primary_genre}:
- EASY: Basic {primary_genre} facts (iconic scenes, main themes, lead roles)
- MEDIUM: Specific {primary_genre} elements (genre techniques, character archetypes, plot devices)
- HARD: Deep {primary_genre} knowledge (genre evolution, directorial style, cultural impact)

Create a {difficulty_word} question that specifically tests {primary_genre} movie knowledge and genre expertise.

Format EXACTLY as:
Q: <your {primary_genre}-focused question>
A. <option 1>
B. <option 2> 
C. <option 3>
D. <option 4>
Answer: <LETTER>

Make it {primary_genre}-specific and genre-relevant!
"""
        return template
    
    def _get_genre_focus_areas(self, genre: str) -> str:
        """Get specific focus areas for different movie genres."""
        genre_guides = {
            "Action": """- High-octane sequences, stunts, and choreography
- Weapon usage, fight scenes, and chase sequences  
- Action heroes, villains, and their motivations
- Special effects, explosions, and practical stunts
- Franchise connections and action movie tropes""",
            
            "Drama": """- Character development and emotional arcs
- Social issues, family dynamics, and relationships
- Dramatic performances and award recognition
- Real-life inspirations and biographical elements
- Dialogue quality and meaningful themes""",
            
            "Comedy": """- Comedic timing, humor styles, and funny scenes
- Comic actors and their signature roles
- Parody elements and satirical themes
- Memorable quotes and comedic situations
- Different comedy sub-genres (rom-com, dark comedy, etc.)""",
            
            "Horror": """- Scare techniques, suspense building, and fear elements
- Horror sub-genres (slasher, psychological, supernatural)
- Iconic horror scenes and jump scares
- Horror movie villains and monsters
- Gore levels, practical effects, and makeup""",
            
            "Thriller": """- Suspense building and tension creation
- Plot twists, mysteries, and reveals
- Psychological elements and mind games
- Chase sequences and cat-and-mouse dynamics
- Paranoia themes and conspiracy elements""",
            
            "Romance": """- Love stories, relationship dynamics, and chemistry
- Romantic leads and their on-screen partnerships
- Meet-cute scenarios and romantic gestures
- Heartbreak, passion, and emotional moments
- Wedding scenes, proposals, and happy endings""",
            
            "Sci-Fi": """- Futuristic concepts, technology, and scientific themes
- Space travel, aliens, and otherworldly elements
- Time travel, dystopian futures, and alternate realities
- Special effects, CGI, and visual innovation
- Scientific accuracy and theoretical concepts""",
            
            "Fantasy": """- Magical elements, mythical creatures, and supernatural powers
- World-building, fictional realms, and fantasy races
- Quests, prophecies, and hero's journey narratives
- Magic systems, spells, and fantasy combat
- Adaptation from fantasy literature and folklore""",
            
            "Crime": """- Criminal activities, heists, and law enforcement
- Detective work, investigations, and forensics
- Organized crime, gangs, and criminal masterminds
- Courtroom dramas and legal procedures
- Moral ambiguity and crime consequences""",
            
            "Western": """- Old West settings, frontier life, and cowboy culture
- Gunfights, saloons, and horseback riding
- Outlaws, sheriffs, and justice themes
- Desert landscapes and small town dynamics
- Native American relations and historical context""",
            
            "War": """- Military tactics, battles, and warfare strategies
- Historical conflicts and war periods
- Soldier experiences, camaraderie, and sacrifice
- War's impact on civilians and families
- Anti-war messages and heroism themes""",
            
            "Animation": """- Animation techniques and visual styles
- Voice acting and character performances
- Family-friendly themes and life lessons
- Studio signatures (Disney, Pixar, Studio Ghibli)
- Technical innovation in animation""",
            
            "Documentary": """- Real-world subjects and factual content
- Documentary filmmaking techniques
- Educational value and information presented
- Interview subjects and expert opinions
- Social impact and awareness raising""",
            
            "Musical": """- Musical numbers, songs, and choreography
- Musical theater adaptations and original scores
- Singing performances and vocal talents
- Dance sequences and performance staging
- Broadway connections and show tunes"""
        }
        
        return genre_guides.get(genre, """- Genre-specific themes and conventions
- Typical character archetypes for this genre
- Common plot devices and storytelling techniques
- Visual and auditory elements characteristic of this genre
- Cultural and historical context of the genre""")

    def _summarize_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return "No prior answers; start with baseline difficulty."
        correct_count = sum(1 for h in history if h.get("correct"))
        last = history[-1]
        trend = "improving" if len(history) > 2 and history[-1].get("correct") and history[-2].get("correct") else "mixed"
        return (
            f"Total answered: {len(history)}, correct: {correct_count}. Last answer was "
            f"{'correct' if last.get('correct') else 'incorrect'}. Performance trend: {trend}."
        )

    def _fallback_generate(self, movie: pd.Series, difficulty_level: int) -> Dict[str, Any]:
        """Generate diverse, contextual questions using movie data when AI is unavailable."""
        difficulty_map = {1: "easy", 2: "medium", 3: "hard"}
        difficulty_word = difficulty_map.get(difficulty_level, "medium")
        
        # Clean movie data
        movie_name = str(movie.get('movie name', 'Unknown')).strip()
        year = str(movie.get('Year', '')).replace('-', '').strip()
        genre = str(movie.get('genre', '')).strip()
        director = str(movie.get('DIRECTOR', '')).strip()
        plot = str(movie.get('DETAIL ABOUT MOVIE', '')).strip()
        rating = str(movie.get('RATING', '')).strip()
        metascore = str(movie.get('metascore', '')).strip()
        runtime = str(movie.get('runtime', '')).strip()
        certificate = str(movie.get('certificate', '')).strip()
        actors = [str(movie.get(f'ACTOR {i}', '')).strip() for i in [1, 2, 3, 4] if str(movie.get(f'ACTOR {i}', '')).strip()]
        
        # Get primary genre for focused questions
        primary_genre = genre.split(',')[0].strip() if genre else "Drama"
        
        # Define question templates by category and difficulty with genre focus
        question_templates = {
            1: [  # Easy questions
                ("year", f"In which year was the {primary_genre.lower()} film '{movie_name}' released?", [year]),
                ("director", f"Who directed the {primary_genre.lower()} movie '{movie_name}'?", [director]),
                ("genre_identification", f"'{movie_name}' is primarily what type of {primary_genre.lower()} film?", [self._get_genre_subtype(primary_genre, plot)]),
                ("lead_actor", f"Who stars in the {primary_genre.lower()} film '{movie_name}'?", [actors[0]] if actors else ["Unknown"]),
                ("genre_theme", f"What {primary_genre.lower()} theme is central to '{movie_name}'?", [self._get_genre_theme(primary_genre, plot)]),
            ],
            2: [  # Medium questions  
                ("genre_elements", f"What {primary_genre.lower()} elements make '{movie_name}' distinctive?", [self._get_genre_elements(primary_genre, plot)]),
                ("genre_comparison", f"'{movie_name}' is similar to which other {primary_genre.lower()} film?", [self._get_genre_similar_movie(primary_genre)]),
                ("genre_technique", f"What {primary_genre.lower()} filmmaking technique is used in '{movie_name}'?", [self._get_genre_technique(primary_genre)]),
                ("genre_character", f"What type of {primary_genre.lower()} character archetype appears in '{movie_name}'?", [self._get_genre_archetype(primary_genre, actors)]),
                ("genre_rating", f"How does '{movie_name}' rate among {primary_genre.lower()} films?", [self._get_genre_rating_context(rating, primary_genre)]),
                ("runtime", f"What is the typical runtime for a {primary_genre.lower()} film like '{movie_name}'?", [self._get_runtime_range(runtime)]),
            ],
            3: [  # Hard questions
                ("genre_innovation", f"How did '{movie_name}' innovate within the {primary_genre.lower()} genre?", [self._get_genre_innovation(primary_genre, year)]),
                ("genre_influence", f"What {primary_genre.lower()} films influenced '{movie_name}'?", [self._get_genre_influence(primary_genre, year)]),
                ("genre_subgenre", f"'{movie_name}' belongs to which {primary_genre.lower()} sub-genre?", [self._get_detailed_subgenre(primary_genre, plot)]),
                ("genre_director_style", f"What {primary_genre.lower()} directorial style does '{director}' use in '{movie_name}'?", [self._get_director_genre_style(primary_genre, director)]),
                ("genre_cultural_impact", f"How did '{movie_name}' impact the {primary_genre.lower()} genre?", [self._get_cultural_impact(primary_genre, year)]),
            ]
        }
        
        # Select random question type for difficulty level
        available_questions = question_templates.get(difficulty_level, question_templates[1])
        question_type, question, correct_answers = random.choice(available_questions)
        
        # Generate options based on question type
        options, correct_idx = self._generate_options(question_type, correct_answers[0], movie, difficulty_level)
        
        return {
            "question": question,
            "options": options,
            "answer_index": correct_idx,
            "difficulty": difficulty_word,
        }
    
    def _generate_options(self, question_type: str, correct_answer: str, movie: pd.Series, difficulty_level: int) -> tuple:
        """Generate 4 options with 1 correct answer based on question type."""
        
        # Common wrong options by category (expanded with genre-specific options)
        wrong_options = {
            "year": ["1995", "2001", "2010", "2015", "1999", "2005", "1990", "2008"],
            "director": ["Christopher Nolan", "Steven Spielberg", "Quentin Tarantino", "Martin Scorsese", "Ridley Scott", "David Fincher"],
            "genre": ["Drama", "Action", "Comedy", "Thriller", "Horror", "Romance", "Sci-Fi", "Adventure"],
            "actor": ["Tom Hanks", "Leonardo DiCaprio", "Brad Pitt", "Robert De Niro", "Al Pacino", "Johnny Depp"],
            "rating_range": ["6.0-7.0", "7.0-8.0", "8.0-9.0", "9.0-10.0"],
            "runtime_range": ["90-120 minutes", "120-150 minutes", "150-180 minutes", "180+ minutes"],
            "decade": ["1980s films", "1990s films", "2000s films", "2010s films"],
            # Genre-specific wrong options
            "genre_themes": ["Revenge and justice", "Love and relationships", "Good vs evil", "Coming of age", "Redemption story"],
            "genre_elements": ["Visual spectacle", "Character development", "Emotional depth", "Technical mastery", "Cultural significance"],
            "genre_movies": ["Citizen Kane", "The Godfather", "Casablanca", "Singin' in the Rain", "2001: A Space Odyssey"],
            "genre_techniques": ["Innovative cinematography", "Masterful editing", "Exceptional sound design", "Outstanding performances", "Creative direction"],
            "genre_archetypes": ["Reluctant hero", "Wise mentor", "Comic relief", "Love interest", "Villain mastermind"],
            "genre_concepts": ["Groundbreaking storytelling", "Cultural phenomenon", "Technical innovation", "Artistic achievement", "Genre evolution"]
        }
        
        if question_type == "NOT_ACTOR":
            # Special case: which actor did NOT appear
            actors = [str(movie.get(f'ACTOR {i}', '')).strip() for i in [1, 2, 3, 4] if str(movie.get(f'ACTOR {i}', '')).strip()]
            fake_actors = ["Tom Hanks", "Leonardo DiCaprio", "Brad Pitt", "Will Smith"]
            fake_actor = random.choice([a for a in fake_actors if a not in actors])
            options = actors[:3] + [fake_actor]
            random.shuffle(options)
            return options, options.index(fake_actor)
        
        # Standard case: generate 3 wrong + 1 correct
        category = self._get_option_category(question_type)
        available_wrong = wrong_options.get(category, wrong_options.get("genre_themes", wrong_options["genre"]))
        
        # Filter out the correct answer from wrong options
        available_wrong = [opt for opt in available_wrong if opt.lower() != correct_answer.lower()]
        
        # Select 3 random wrong options
        wrong_selected = random.sample(available_wrong, min(3, len(available_wrong)))
        
        # Ensure we have exactly 3 wrong options
        while len(wrong_selected) < 3:
            wrong_selected.append(f"Option {len(wrong_selected) + 1}")
        
        # Create final options list
        options = wrong_selected + [correct_answer]
        random.shuffle(options)
        
        return options, options.index(correct_answer)
    
    def _get_option_category(self, question_type: str) -> str:
        """Map question types to option categories."""
        mapping = {
            "year": "year", "year_context": "decade",
            "director": "director", "lead_actor": "actor", "supporting_actor": "actor",
            "genre": "genre", "genre_combo": "genre", "genre_identification": "genre",
            "rating_range": "rating_range", "runtime": "runtime_range",
            "metascore": "rating_range", "genre_rating": "rating_range",
            # New genre-specific mappings
            "genre_theme": "genre_themes", "genre_elements": "genre_elements",
            "genre_comparison": "genre_movies", "genre_technique": "genre_techniques",
            "genre_character": "genre_archetypes", "genre_innovation": "genre_concepts",
            "genre_influence": "genre_movies", "genre_subgenre": "genre",
            "genre_director_style": "genre_techniques", "genre_cultural_impact": "genre_concepts"
        }
        return mapping.get(question_type, "genre")
    
    def _get_rating_range(self, rating: str) -> str:
        """Convert numeric rating to range."""
        try:
            r = float(rating)
            if r >= 9.0: return "9.0-10.0"
            elif r >= 8.0: return "8.0-9.0" 
            elif r >= 7.0: return "7.0-8.0"
            else: return "6.0-7.0"
        except:
            return "7.0-8.0"
    
    def _get_runtime_range(self, runtime: str) -> str:
        """Convert runtime to range."""
        try:
            minutes = int(''.join(filter(str.isdigit, runtime)))
            if minutes >= 180: return "180+ minutes"
            elif minutes >= 150: return "150-180 minutes"
            elif minutes >= 120: return "120-150 minutes"
            else: return "90-120 minutes"
        except:
            return "120-150 minutes"
    
    def _get_metascore_range(self, metascore: str) -> str:
        """Convert metascore to range."""
        try:
            score = int(metascore)
            if score >= 80: return "80-100 (Universal acclaim)"
            elif score >= 60: return "60-79 (Generally positive)"
            elif score >= 40: return "40-59 (Mixed reviews)"
            else: return "Below 40 (Poor reviews)"
        except:
            return "60-79 (Generally positive)"
    
    def _get_plot_theme(self, plot: str) -> str:
        """Extract main theme from plot."""
        plot_lower = plot.lower()
        if "love" in plot_lower or "romance" in plot_lower: return "A romantic story"
        elif "war" in plot_lower or "battle" in plot_lower: return "A war/conflict narrative"
        elif "crime" in plot_lower or "murder" in plot_lower: return "A crime thriller"
        elif "family" in plot_lower: return "A family drama"
        else: return "A character-driven story"
    
    def _get_plot_detail(self, plot: str) -> str:
        """Extract specific plot element."""
        if len(plot) > 50:
            # Extract key phrases or return generic
            words = plot.split()
            if len(words) > 10:
                return " ".join(words[5:15]) + "..."
        return "Character relationships and conflicts"
    
    def _get_decade_context(self, year: str) -> str:
        """Get decade context for the year."""
        try:
            y = int(year)
            decade = (y // 10) * 10
            return f"{decade}s films"
        except:
            return "2000s films"
    
    def _get_technical_aspect(self, genre: str, rating: str) -> str:
        """Get technical/thematic aspect based on genre and rating."""
        if "action" in genre.lower(): return "High-octane action sequences"
        elif "drama" in genre.lower(): return "Character development and emotions"
        elif "comedy" in genre.lower(): return "Humor and comedic timing"
        else: return "Cinematic storytelling techniques"
    
    def _get_similar_movie(self, genre: str) -> str:
        """Suggest similar movie based on genre."""
        similar_movies = {
            "Action": "Die Hard series",
            "Drama": "The Shawshank Redemption", 
            "Comedy": "Groundhog Day",
            "Horror": "The Exorcist",
            "Romance": "Casablanca",
            "Sci-Fi": "Blade Runner"
        }
        return similar_movies.get(genre.split(',')[0].strip(), "Classic cinema")
    
    # Genre-specific helper methods for focused question generation
    def _get_genre_subtype(self, genre: str, plot: str) -> str:
        """Determine the subtype within a genre."""
        genre_subtypes = {
            "Action": "High-octane thriller",
            "Drama": "Character-driven story", 
            "Comedy": "Situational comedy",
            "Horror": "Psychological thriller",
            "Romance": "Romantic drama",
            "Sci-Fi": "Science fiction adventure",
            "Thriller": "Suspense thriller",
            "Crime": "Crime thriller",
            "Western": "Classic western",
            "War": "War drama"
        }
        return genre_subtypes.get(genre, "Drama")
    
    def _get_genre_theme(self, genre: str, plot: str) -> str:
        """Get the main theme typical for the genre."""
        genre_themes = {
            "Action": "Good vs evil conflict",
            "Drama": "Human relationships",
            "Comedy": "Humor and life lessons", 
            "Horror": "Fear and survival",
            "Romance": "Love conquers all",
            "Sci-Fi": "Technology and humanity",
            "Thriller": "Suspense and mystery",
            "Crime": "Justice and morality",
            "Western": "Frontier justice",
            "War": "Honor and sacrifice"
        }
        return genre_themes.get(genre, "Character development")
    
    def _get_genre_elements(self, genre: str, plot: str) -> str:
        """Get distinctive elements for the genre."""
        genre_elements = {
            "Action": "Explosive action sequences",
            "Drama": "Emotional character arcs",
            "Comedy": "Comedic timing and wit",
            "Horror": "Suspenseful atmosphere",
            "Romance": "Romantic chemistry",
            "Sci-Fi": "Futuristic concepts",
            "Thriller": "Edge-of-seat tension",
            "Crime": "Criminal investigations",
            "Western": "Frontier landscapes",
            "War": "Combat realism"
        }
        return genre_elements.get(genre, "Strong storytelling")
    
    def _get_genre_similar_movie(self, genre: str) -> str:
        """Get similar movies within the same genre."""
        genre_comparisons = {
            "Action": "Mission Impossible series",
            "Drama": "Forrest Gump",
            "Comedy": "The Hangover",
            "Horror": "Halloween franchise", 
            "Romance": "The Notebook",
            "Sci-Fi": "Star Wars saga",
            "Thriller": "North by Northwest",
            "Crime": "Goodfellas",
            "Western": "The Good, the Bad and the Ugly",
            "War": "Saving Private Ryan"
        }
        return genre_comparisons.get(genre, "Similar acclaimed films")
    
    def _get_genre_technique(self, genre: str) -> str:
        """Get filmmaking techniques typical for the genre."""
        genre_techniques = {
            "Action": "Dynamic camera work",
            "Drama": "Character-focused cinematography",
            "Comedy": "Comedic timing and editing",
            "Horror": "Suspenseful sound design",
            "Romance": "Intimate cinematography",
            "Sci-Fi": "Visual effects mastery",
            "Thriller": "Tension-building editing",
            "Crime": "Noir-style lighting",
            "Western": "Wide landscape shots",
            "War": "Realistic battle choreography"
        }
        return genre_techniques.get(genre, "Cinematic storytelling")
    
    def _get_genre_archetype(self, genre: str, actors: list) -> str:
        """Get character archetypes typical for the genre."""
        genre_archetypes = {
            "Action": "Action hero protagonist",
            "Drama": "Complex character study",
            "Comedy": "Comedic lead character",
            "Horror": "Survivor protagonist",
            "Romance": "Romantic lead couple",
            "Sci-Fi": "Reluctant hero",
            "Thriller": "Ordinary person in danger",
            "Crime": "Antihero protagonist",
            "Western": "Lone gunslinger",
            "War": "Soldier protagonist"
        }
        return genre_archetypes.get(genre, "Central character")
    
    def _get_genre_rating_context(self, rating: str, genre: str) -> str:
        """Get rating context within the genre."""
        try:
            r = float(rating)
            if r >= 8.5: return f"Top-tier {genre.lower()} film"
            elif r >= 7.5: return f"Well-regarded {genre.lower()} movie"
            elif r >= 6.5: return f"Decent {genre.lower()} entry"
            else: return f"Average {genre.lower()} film"
        except:
            return f"Notable {genre.lower()} movie"
    
    def _get_genre_innovation(self, genre: str, year: str) -> str:
        """Get how the film innovated within its genre."""
        return f"Advanced {genre.lower()} filmmaking techniques"
    
    def _get_genre_influence(self, genre: str, year: str) -> str:
        """Get films that influenced this one within the genre."""
        return f"Classic {genre.lower()} cinema traditions"
    
    def _get_detailed_subgenre(self, genre: str, plot: str) -> str:
        """Get specific sub-genre classification."""
        subgenres = {
            "Action": "Superhero action",
            "Drama": "Social drama", 
            "Comedy": "Romantic comedy",
            "Horror": "Psychological horror",
            "Thriller": "Political thriller",
            "Sci-Fi": "Space opera",
            "Crime": "Heist thriller"
        }
        return subgenres.get(genre, f"{genre} drama")
    
    def _get_director_genre_style(self, genre: str, director: str) -> str:
        """Get the director's style within the genre."""
        return f"Distinctive {genre.lower()} direction"
    
    def _get_cultural_impact(self, genre: str, year: str) -> str:
        """Get the cultural impact within the genre."""
        return f"Influenced modern {genre.lower()} films"

    def generate_question(self, difficulty_level: int, history: List[Dict[str, Any]], preferred_genre: str = None) -> Dict[str, Any]:
        movie = self._select_movie_row(difficulty_level, preferred_genre)
        # If no kernel (no API key) use fallback.
        if self.kernel is None or self.chat_service is None or self.execution_settings is None:
            return self._fallback_generate(movie, difficulty_level)

        prompt = self._build_prompt(movie, difficulty_level, history)
        if ChatHistory is None:
            return self._fallback_generate(movie, difficulty_level)
        chat_history = ChatHistory()
        # Different versions use add_user_message or add_message
        if hasattr(chat_history, 'add_user_message'):
            chat_history.add_user_message(prompt)
        else:
            # Fallback generic attribute
            chat_history.add_message('user', prompt)  # type: ignore
        try:
            response = self.chat_service.get_chat_message_content(  # type: ignore
                chat_history=chat_history, settings=self.execution_settings  # type: ignore
            )
            # response may be list or single
            if isinstance(response, list):
                content = response[0].content
            else:
                content = response.content  # type: ignore
        except Exception as e:
            # Fallback on failure
            return self._fallback_generate(movie, difficulty_level)

        parsed_result = self._parse_llm_output(content)
        
        # Validate the result and use fallback if necessary
        if not self._validate_question(parsed_result, movie):
            print(f"AI question validation failed, using fallback for {movie.get('movie name', 'Unknown')}")
            return self._fallback_generate(movie, difficulty_level)
            
        return parsed_result
    
    def _validate_question(self, question_data: Dict[str, Any], movie: pd.Series) -> bool:
        """Validate that the generated question makes sense."""
        try:
            question = question_data.get("question", "")
            options = question_data.get("options", [])
            answer_index = question_data.get("answer_index", 0)
            
            # Basic validation
            if len(question) < 10:
                return False
            if len(options) != 4:
                return False
            if answer_index < 0 or answer_index >= 4:
                return False
            
            # Check if question mentions the movie
            movie_name = str(movie.get('movie name', '')).strip()
            if movie_name and len(movie_name) > 3:
                if movie_name.lower() not in question.lower():
                    return False
            
            # Check that options are not empty or too short
            for option in options:
                if not option or len(option.strip()) < 2:
                    return False
            
            return True
            
        except Exception:
            return False

    def _parse_llm_output(self, text: str) -> Dict[str, Any]:
        """Parse AI response with robust error handling and validation."""
        try:
            # Clean the text
            text = text.strip()
            
            # Extract question - try multiple patterns
            question = None
            question_patterns = [
                r"Q:\s*(.+?)(?=\n[A-D]\.|$)",  # Q: question until option A-D
                r"Question:\s*(.+?)(?=\n[A-D]\.|$)",  # Question: alternative
                r"\*\*Question\*\*:\s*(.+?)(?=\n[A-D]\.|$)",  # **Question**: markdown
            ]
            
            for pattern in question_patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    question = match.group(1).strip().replace('\n', ' ')
                    break
            
            if not question:
                # Fallback: take first line as question
                lines = text.split('\n')
                question = lines[0].strip() if lines else "Unable to parse question"
            
            # Extract options - more robust parsing
            options = []
            option_patterns = [
                r"([A-D])\.\s*(.+?)(?=\n[A-D]\.|\nAnswer:|$)",  # A. option
                r"\*\*([A-D])\*\*[\.:)]\s*(.+?)(?=\n[A-D]\.|\nAnswer:|$)",  # **A**: option
            ]
            
            found_options = {}
            for pattern in option_patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
                for letter, option_text in matches:
                    found_options[letter.upper()] = option_text.strip().replace('\n', ' ')
            
            # Ensure we have all 4 options
            for letter in ['A', 'B', 'C', 'D']:
                if letter in found_options:
                    options.append(found_options[letter])
                else:
                    options.append(f"Option {letter}")
            
            # Extract answer - try multiple patterns
            answer_letter = 'A'  # Default
            answer_patterns = [
                r"Answer:\s*([A-D])",
                r"Correct.*?:\s*([A-D])",
                r"\*\*Answer\*\*:\s*([A-D])",
                r"The correct answer is\s*([A-D])"
            ]
            
            for pattern in answer_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    answer_letter = match.group(1).upper()
                    break
            
            # Validate answer letter
            if answer_letter not in ['A', 'B', 'C', 'D']:
                answer_letter = 'A'
            
            answer_index = ['A', 'B', 'C', 'D'].index(answer_letter)
            
            # Validate that we have reasonable content
            if len(question) < 10:
                question = "Unable to parse question properly"
            
            return {
                "question": question,
                "options": options,
                "answer_index": answer_index,
                "difficulty": "unknown",
                "raw_response": text[:200] + "..." if len(text) > 200 else text  # For debugging
            }
            
        except Exception as e:
            # Complete fallback
            return {
                "question": "Error parsing AI response",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer_index": 0,
                "difficulty": "unknown",
                "error": str(e)
            }

