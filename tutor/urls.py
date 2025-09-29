from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'circuits', views.QuantumCircuitViewSet, basename='circuit')
router.register(r'qa-sessions', views.QASessionViewSet, basename='qasession')
router.register(r'quizzes', views.QuizQuestionViewSet, basename='quiz')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    
    # Web routes
    path('', views.dashboard, name='dashboard'),
    path('circuits/create/', views.circuit_create, name='circuit_create'),
    path('circuits/<int:circuit_id>/', views.circuit_detail, name='circuit_detail'),
    path('circuits/<int:circuit_id>/simulation/', views.simulation_view, name='simulation'),
    path('qa/', views.qa_view, name='qa'),
    
    # API endpoints for specific actions
    path('api/circuits/<int:circuit_id>/parse/', 
         views.QuantumCircuitViewSet.as_view({'post': 'parse_circuit'}), 
         name='circuit-parse'),
    path('api/circuits/<int:circuit_id>/simulate/', 
         views.QuantumCircuitViewSet.as_view({'post': 'simulate'}), 
         name='circuit-simulate'),
    path('api/qa/ask/', 
         views.QASessionViewSet.as_view({'post': 'ask_question'}), 
         name='qa-ask'),
    path('api/circuits/<int:circuit_id>/execute_code/', 
         views.QuantumCircuitViewSet.as_view({'post': 'execute_code'}), 
         name='circuit-execute-code'),
]