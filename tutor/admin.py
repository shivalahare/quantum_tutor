from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, QuantumCircuit, CircuitGate, Explanation,
    SimulationResult, QASession, QuizQuestion
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'difficulty_level', 'is_staff')
    list_filter = ('difficulty_level', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Quantum Tutor', {'fields': ('difficulty_level',)}),
    )

class CircuitGateInline(admin.TabularInline):
    model = CircuitGate
    extra = 0

@admin.register(QuantumCircuit)
class QuantumCircuitAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'num_qubits', 'created_at')
    list_filter = ('created_at', 'num_qubits')
    search_fields = ('title', 'qiskit_code')
    inlines = [CircuitGateInline]

@admin.register(CircuitGate)
class CircuitGateAdmin(admin.ModelAdmin):
    list_display = ('gate_type', 'circuit', 'step_order', 'qubits_display')
    list_filter = ('gate_type', 'circuit')
    
    def qubits_display(self, obj):
        return str(obj.qubits)
    qubits_display.short_description = 'Qubits'

@admin.register(Explanation)
class ExplanationAdmin(admin.ModelAdmin):
    list_display = ('gate_type', 'difficulty_level', 'created_at')
    list_filter = ('gate_type', 'difficulty_level')
    search_fields = ('explanation_text',)

@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ('circuit', 'shots', 'created_at')
    list_filter = ('created_at',)

@admin.register(QASession)
class QASessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('question', 'answer')
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('circuit', 'difficulty_level', 'created_at')
    list_filter = ('difficulty_level', 'created_at')