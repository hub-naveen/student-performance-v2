# Student Performance Prediction System

A comprehensive web application for predicting student academic performance using machine learning, with role-based dashboards for students, teachers, and administrators.

## Features

### 🎯 Core Functionality
- **Machine Learning Predictions**: Advanced ML models for academic performance prediction
- **Role-Based Access Control**: Separate interfaces for students, teachers, and administrators
- **Real-time Notifications**: Automated alerts and notifications system
- **Comprehensive Analytics**: Detailed performance analytics and reporting
- **Responsive Design**: Mobile-friendly interface with modern UI/UX

### 👥 User Roles

#### Students
- Personal academic dashboard
- Grade tracking and trends
- Attendance monitoring
- Assignment due dates
- Performance predictions
- Personalized recommendations

#### Teachers
- Class management
- Student performance overview
- Assignment creation and grading
- Attendance tracking
- Predictive analytics for intervention
- Recommendation system

#### Administrators
- System-wide analytics
- User management
- ML model management
- Notification system configuration
- Comprehensive reporting
- System health monitoring

## Technology Stack

### Backend
- **Framework**: Django 4.2 with Django REST Framework
- **Database**: PostgreSQL with optimized indexes
- **Authentication**: JWT with OAuth2 support
- **ML Framework**: scikit-learn with joblib for model persistence
- **Task Queue**: Celery with Redis
- **API Documentation**: Swagger/OpenAPI
- **Security**: CORS, CSRF protection, rate limiting

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router DOM
- **State Management**: Context API
- **UI Components**: Tailwind CSS with Headless UI
- **Charts**: Recharts for data visualization
- **HTTP Client**: Axios with interceptors
- **Notifications**: React Hot Toast

### Infrastructure
- **Containerization**: Docker with Docker Compose
- **Web Server**: Gunicorn with Whitenoise
- **Caching**: Redis for session and cache management
- **Email**: SMTP integration for notifications
- **File Storage**: Local storage with media handling

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd student-performance-system
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database and email settings
   ```

4. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Load sample data (optional)**
   ```bash
   python manage.py loaddata fixtures/sample_data.json
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm run dev
   ```

### Docker Setup (Recommended)

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## Database Schema

### Core Models

#### Users & Authentication
- **User**: Extended user model with role-based access
- **EmailVerificationToken**: Email verification system
- **PasswordResetToken**: Secure password reset
- **UserSession**: Session tracking for security
- **AuditLog**: Comprehensive audit logging

#### Student Management
- **StudentProfile**: Extended student information
- **Subject**: Academic subjects and courses
- **Class**: Class instances with enrollment management
- **Enrollment**: Student-class relationships
- **Assignment**: Assignment management
- **Grade**: Grade tracking with analytics
- **Attendance**: Attendance monitoring
- **BehaviorRecord**: Behavioral incident tracking

#### ML & Predictions
- **PredictionModel**: ML model versioning and management
- **PerformancePrediction**: Individual predictions with confidence scores
- **Recommendation**: AI-generated intervention recommendations
- **ModelPerformanceMetric**: Model evaluation tracking
- **PredictionFeedback**: User feedback on predictions

#### Notifications
- **NotificationTemplate**: Reusable notification templates
- **Notification**: Individual notification instances
- **NotificationRule**: Automated notification triggers
- **NotificationPreference**: User notification preferences
- **AlertSubscription**: Targeted alert subscriptions

## Machine Learning Pipeline

### Model Features
- GPA and grade trends
- Attendance patterns
- Assignment completion rates
- Behavioral indicators
- Demographic factors
- Extracurricular participation

### Prediction Types
- **Grade Prediction**: Semester/course grade forecasting
- **Dropout Risk**: Early warning system
- **Graduation Likelihood**: Long-term success prediction
- **Subject Performance**: Subject-specific predictions

### Model Management
- Version control for ML models
- A/B testing capabilities
- Performance monitoring
- Automated retraining pipelines

## Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- OAuth2 integration
- Session management
- Account lockout protection

### Data Protection
- SQL injection prevention
- XSS protection
- CSRF tokens
- Input validation and sanitization
- Secure password policies
- Rate limiting

### Audit & Compliance
- Comprehensive audit logging
- User activity tracking
- Data access monitoring
- GDPR compliance features

## Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   # Set production environment variables
   export DEBUG=False
   export SECRET_KEY=your-production-secret-key
   export DATABASE_URL=postgresql://user:pass@host:port/db
   ```

2. **Database Migration**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

3. **Start Services**
   ```bash
   # Web server
   gunicorn student_performance.wsgi:application

   # Background tasks
   celery -A student_performance worker -l info
   celery -A student_performance beat -l info
   ```

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `GET /api/v1/auth/profile/` - Get user profile
- `PATCH /api/v1/auth/profile/` - Update profile

### Students
- `GET /api/v1/students/dashboard/student/` - Student dashboard
- `GET /api/v1/students/dashboard/teacher/` - Teacher dashboard
- `GET /api/v1/students/profiles/` - Student profiles
- `GET /api/v1/students/classes/` - Classes
- `GET /api/v1/students/grades/` - Grades
- `GET /api/v1/students/assignments/` - Assignments

### Predictions
- `GET /api/v1/predictions/predictions/` - Get predictions
- `POST /api/v1/predictions/predictions/batch_predict/` - Batch predictions
- `GET /api/v1/predictions/recommendations/` - Get recommendations
- `POST /api/v1/predictions/recommendations/generate_from_prediction/` - Generate recommendations
- `GET /api/v1/predictions/analytics/` - Prediction analytics

### Notifications
- `GET /api/v1/notifications/notifications/` - Get notifications
- `POST /api/v1/notifications/notifications/mark_as_read/` - Mark as read
- `GET /api/v1/notifications/preferences/` - Get preferences
- `PATCH /api/v1/notifications/preferences/` - Update preferences

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all React components
- Write comprehensive tests
- Update documentation for new features
- Follow semantic versioning

## Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API documentation at `/swagger/`

## Roadmap

### Upcoming Features
- [ ] Mobile app development
- [ ] Advanced ML models (deep learning)
- [ ] Real-time collaboration features
- [ ] Integration with LMS platforms
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Parent portal
- [ ] Automated report generation

### Performance Improvements
- [ ] Database query optimization
- [ ] Caching layer enhancement
- [ ] API response optimization
- [ ] Frontend bundle optimization