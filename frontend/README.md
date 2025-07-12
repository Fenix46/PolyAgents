# PolyAgents Frontend

A modern React application for the PolyAgents multi-agent AI system, featuring real-time chat, agent monitoring, and conversation management.

## 🚀 Features

- **Real-time Chat Interface**: Live conversation with multiple AI agents
- **Agent Status Panel**: Monitor agent activity and system health
- **Conversation Management**: Browse, search, and manage conversations
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Modern dark theme optimized for long sessions
- **WebSocket Integration**: Real-time updates for agent responses and status

## 🛠️ Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Shadcn/ui** for UI components
- **React Query** for state management
- **WebSocket** for real-time updates
- **React Router** for navigation

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## ⚙️ Configuration

### Environment Variables

Create environment files for different environments:

#### Development (`env.development`)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000/ws
VITE_API_KEY=pa_dev_key_123
```

#### Production (`env.production`)
```env
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost/ws
VITE_API_KEY=pa_your_secret_key_here
```

### API Configuration

The frontend connects to the PolyAgents backend API through:

- **REST API**: For chat, conversations, and system health
- **WebSocket**: For real-time updates and agent status

## 🏗️ Architecture

```
src/
├── components/          # UI components
│   ├── ui/             # Shadcn/ui components
│   ├── layout/         # Layout components (Header, Sidebar)
│   ├── chat/           # Chat interface components
│   └── agents/         # Agent status components
├── pages/              # Route components
├── services/           # API and WebSocket services
├── hooks/              # Custom React hooks
├── types/              # TypeScript definitions
└── lib/                # Utility functions
```

## 🔧 Development

### Project Structure

- **Components**: Modular UI components with TypeScript interfaces
- **Services**: API client and WebSocket service for backend communication
- **Hooks**: Custom hooks for state management and API integration
- **Types**: TypeScript definitions for all data structures

### Key Components

- **ChatInterface**: Main chat component with message display and input
- **AgentStatusPanel**: Real-time agent monitoring and system health
- **Sidebar**: Conversation management and navigation
- **Header**: Application header with connection status

### State Management

The application uses React Query for server state and local state for UI:

- **API State**: Managed by React Query for caching and synchronization
- **WebSocket State**: Real-time updates for agent status and messages
- **UI State**: Local state for sidebar collapse, modals, etc.

## 🚀 Deployment

### Docker Deployment

The frontend is containerized with nginx for production:

```bash
# Build the frontend container
docker build -t polyagents-frontend .

# Run with docker-compose
docker-compose up -d frontend
```

### Nginx Configuration

The production build uses nginx with:

- **Static file serving**: Optimized for React SPA
- **API proxy**: Routes `/api/*` to backend
- **WebSocket proxy**: Routes `/ws/*` to backend
- **Gzip compression**: For better performance
- **Caching**: For static assets

### Environment Setup

1. Configure environment variables in `env.production`
2. Build the application: `npm run build`
3. Deploy with Docker or serve static files

## 🔌 API Integration

### REST API Endpoints

- `POST /api/chat` - Send message to agents
- `GET /api/conversations/recent` - Get recent conversations
- `GET /api/conversations/{id}` - Get conversation details
- `POST /api/conversations/search` - Search conversations
- `GET /api/health/detailed` - System health check
- `GET /api/statistics` - System statistics

### WebSocket Events

- `message` - New message from agent
- `agent_status` - Agent status update
- `consensus_update` - Consensus progress update
- `system_update` - System status update
- `error` - Error notification

## 🎨 Styling

The application uses Tailwind CSS with a custom design system:

- **Color Scheme**: Dark theme optimized for AI chat
- **Components**: Shadcn/ui components for consistency
- **Responsive**: Mobile-first responsive design
- **Animations**: Framer Motion for smooth transitions

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

## 📝 Contributing

1. Follow the existing code style and TypeScript conventions
2. Add proper TypeScript types for all new components
3. Update the documentation for new features
4. Test thoroughly before submitting changes

## 🔗 Links

- **Backend API**: [PolyAgents Backend](../README.md)
- **Documentation**: [API Documentation](../README.md#api-endpoints)
- **Docker Setup**: [Docker Deployment](../README.md#docker-deployment)
