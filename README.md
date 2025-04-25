# Personal Finance Assistant Agent Swarm

<video src="assets/demo-video.mp4" controls width="600" style="display:block;margin-bottom:16px;">
  Your browser does not support the video tag.
</video>

A multi-agent AI system to help users manage personal finances, powered by generative AI technology. This system includes three specialized agents: Budget Planner, Investment Advisor, and Fraud Detector. The agents work together to provide comprehensive financial guidance in simple, easy-to-understand terms.

## Key Features

- **Budget Planning**: Analyzes spending patterns and suggests personalized budgets
- **Investment Advising**: Recommends low-risk investment options based on market trends
- **Fraud Detection**: Flags suspicious transactions using anomaly detection
- **Multilingual Support**: Explains financial advice in simple terms across multiple languages
- **Comprehensive Dashboard**: User-friendly interface to interact with all agents

## Architecture

This project follows a modular architecture with the following components:

- **Backend**: FastAPI for handling requests, authentication, and API endpoints
- **Agent Swarm**: Autogen/LangGraph for managing agent interactions and orchestrating decisions
- **Data Analysis**: Pandas/Numpy for analyzing financial data patterns
- **Explanations**: Hugging Face Transformers for generating natural language explanations
- **Data Storage**: MongoDB for secure storage of user financial data
- **Frontend**: React.js for the user interface (separate repository)

## Prerequisites

- Python 3.9+
- MongoDB 5.0+
- Node.js 16+ (for frontend)

## Getting Started

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/personal-finance-management.git
   cd personal-finance-management
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
   - Copy `.env.example` to `.env`
   - Edit the variables to match your configuration

5. Set up MongoDB:
   ```
   # Make sure MongoDB is running on localhost:27017
   # The application will automatically create collections as needed
   ```

6. Run the server:
   ```
   uvicorn app.main:app --reload
   ```

7. Access the API documentation: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/token` - Login and get access token

### Budget Planning
- `GET /api/v1/budget/summary` - Get budget summary
- `POST /api/v1/budget/advice` - Get personalized budget advice
- `GET /api/v1/budget/transactions` - List transactions
- `POST /api/v1/budget/transactions` - Add a new transaction

### Investment
- `GET /api/v1/investment/recommendations` - Get investment recommendations
- `GET /api/v1/investment/market-trends` - Get current market trends
- `GET /api/v1/investment/portfolio` - View investment portfolio
- `POST /api/v1/investment/portfolio` - Add to investment portfolio

### Fraud Detection
- `POST /api/v1/fraud/scan-transactions` - Scan transactions for fraud
- `POST /api/v1/fraud/report-transaction/{transaction_id}` - Report suspicious transaction

## Agent Architecture

The system uses three specialized agents that communicate with each other:

1. **Budget Planner Agent**: Analyzes spending patterns and recommends personalized budgets
2. **Investment Advisor Agent**: Recommends low-risk investments based on market trends and user goals
3. **Fraud Detector Agent**: Identifies suspicious transactions using anomaly detection

These agents are orchestrated by a central coordination system that routes user requests and integrates responses.

## Development

### Project Structure

```
├── app/
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Environment variables and configuration
│   ├── api/                   # API endpoints
│   │   ├── routes/
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── budget.py      # Budget planning endpoints
│   │   │   ├── investment.py  # Investment advice endpoints
│   │   │   └── fraud.py       # Fraud detection endpoints
│   ├── agents/                # Agent implementations
│   │   ├── budget_agent.py    # Budget planner implementation
│   │   ├── investment_agent.py # Investment advisor implementation
│   │   ├── fraud_agent.py     # Fraud detector implementation 
│   │   └── orchestrator.py    # LangGraph agent coordination
│   ├── models/                # Data models
│   │   ├── database.py        # Database connection setup
│   │   ├── user.py            # User model
│   │   ├── transaction.py     # Transaction model
│   │   └── portfolio.py       # Investment portfolio model
│   ├── schemas/               # Pydantic schemas for API validation
│   ├── services/              # Business logic and external services
│   └── utils/                 # Utility functions
├── data/                      # Mock and seed data
├── tests/                     # Test modules
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

### Adding a New Agent

1. Create a new agent file in the `app/agents/` directory
2. Implement the agent logic using the Autogen framework
3. Register the agent in the `orchestrator.py` file
4. Add corresponding API endpoints in the `app/api/routes/` directory

### Testing

Run the test suite:

```
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

© 2025 FinanceManager - Personal Finance Management. All rights reserved.

## Acknowledgements

- [Autogen](https://github.com/microsoft/autogen) - Multi-agent conversation framework
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Hugging Face Transformers](https://huggingface.co/transformers/) - NLP models
- [Pandas](https://pandas.pydata.org/) - Data analysis
