from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import math


class TrainingPreferences(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    puzzles_per_cycle = models.PositiveIntegerField(default=105)


class Theme(models.Model):
    name = models.CharField(max_length=100, unique=True)
    lichess_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} - {self.lichess_name}"


class TrainingCycle(models.Model):
    """
    Ciclo de entrenamiento estilo Botvinnik
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()

    total = models.PositiveIntegerField(
        help_text="Cantidad total de ejercicios del ciclo"
    )

    completed = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def _create_cycle_themes(self):

        if self.themes.exists():
            return

        theme_elos = ThemeElo.objects.filter(user=self.user)

        if theme_elos.count() == 0:
            return

        weak_themes = theme_elos.order_by("elo")[:2]

        strong_theme = (
            theme_elos
            .exclude(theme__in=[t.theme for t in weak_themes])
            .order_by("-elo")
            .first()
        )

        with transaction.atomic():
            for priority, theme_elo in enumerate(weak_themes, start=1):
                TrainingCycleTheme.objects.create(
                    cycle=self,
                    theme=theme_elo.theme,
                    priority=priority,
                )

            if strong_theme:
                TrainingCycleTheme.objects.create(
                    cycle=self,
                    theme=strong_theme.theme,
                    priority=3,
                )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            self._create_cycle_themes()


class TrainingCycleTheme(models.Model):
    cycle = models.ForeignKey(
        TrainingCycle,
        on_delete=models.CASCADE,
        related_name="themes"
    )
    theme = models.ForeignKey(
        Theme,
        on_delete=models.CASCADE
    )

    priority = models.PositiveSmallIntegerField(
        default=1,
        help_text="1 = máxima prioridad"
    )

    class Meta:
        unique_together = ("cycle", "theme")


class BaseElo(models.Model):
    elo = models.IntegerField(default=1500)
    puzzles_played = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def expected_score(self, opponent_elo: int) -> float:
        return 1 / (1 + math.pow(10, (opponent_elo - self.elo) / 400))

    def k_factor(self) -> int:
        """
        K-factor simple:
        - Más alto al inicio
        - Más estable con experiencia
        """
        if self.puzzles_played < 30:
            return 40
        if self.elo < 2000:
            return 20
        return 10

    def update_elo(self, opponent_elo: int, score: float):
        """
        score:
        - 1.0 = win
        - 0.0 = loss
        """
        expected = self.expected_score(opponent_elo)
        k = self.k_factor()

        self.elo = round(self.elo + k * (score - expected))
        self.puzzles_played += 1
        self.save(update_fields=["elo", "puzzles_played", "last_updated"])


class Elo(BaseElo):
    """Elo general del usuario"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.user} - Elo {self.elo}"


class ThemeElo(BaseElo):
    """Elo por tema"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "theme")

    def __str__(self):
        return f"Elo de {self.user} - {self.theme}: ({self.elo})"


class DailyProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    date = models.DateField()
    solved = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")


class PuzzleAttempt(models.Model):
    """
    Historial de puzzles realizados por el usuario
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    puzzle_id = models.CharField(max_length=100)
    theme_origin = models.ForeignKey(
        Theme, on_delete=models.SET_NULL, null=True)
    solved = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)


class ActiveExercise(models.Model):
    """
    Ejercicio actualmente asignado al usuario.
    Solo puede existir uno por usuario.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="active_exercise"
    )

    puzzle_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class PuzzleTraining(models.Model):
    """
    Puzzles que el usuario falló y debe volver a realizar
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    puzzle_id = models.CharField(max_length=100)
    theme_origin = models.ForeignKey(
        Theme, on_delete=models.SET_NULL, null=True)
    solved = models.BooleanField(default=False)
    fail_count = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "puzzle_id")


class TrainingStreak(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_training_date = models.DateField(auto_now=True)
