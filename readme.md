# Ritter Sport Production Load Balancing System

A **decision support tool** that transforms manual production planning from educated guesses into data-driven optimization, helping production planners optimize weekly load distribution across Monday-Friday and 5 production lines.

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# 1. Clone the repository
git clone <repository-url>
cd anlage_data

# 2. Start the application with Docker
./deploy.sh
# OR: docker compose up --build

# 3. Open your browser
open http://localhost:8501

# 4. Try the demo
Click "Load Sample Scenario" to see the system in action
```

### Option 2: Local Development
```bash
# 1. Set up Python environment
conda activate py310  # or create: conda create -n py310 python=3.10

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
streamlit run src/interface/planner_app.py

# 4. Open your browser
open http://localhost:8501
```

## 🎯 What This System Does

### The Problem
Production managers meet weekly to discuss production requirements, but translating these into actual schedules is done **manually through educated guesses**, leading to:
- Suboptimal load distribution across weekdays and lines
- Resource inefficiency and unpredictable work hours
- Increased costs and difficulty meeting deadlines

### The Solution
Our system provides **intelligent, data-driven decision support** by:

**Input** → **Process** → **Output**
- 📝 **Requirements**: Products, quantities, priorities, deadlines
- ⚙️ **Constraints**: Line availability, operational rules
- 🔮 **Forecasting**: Historical data + domain insights → initial schedule
- ⚖️ **Optimization**: Load balancing while respecting all constraints
- 📊 **Results**: Optimized weekly schedule with clear rationale

## 🏭 Production Context

- **5 Production Lines**: hohl2, hohl3, hohl4, massiv2, massiv3
- **3 Shifts/Day**: Maximum 24 hours per line per day
- **Key Constraints**: 
  - At least 1 line idle per day (backup capacity)
  - Max 1 personnel-intensive line per day
  - Deadline compliance for all products
- **Sample Products**: Standard chocolate, Knusperkeks, Waffel, Marzipan

## 🔧 Key Features

### ✨ Intelligent Forecasting
- **Historical Analysis**: Learns from past production patterns
- **Product-Aware Scheduling**: Considers priorities, deadlines, personnel requirements
- **Constraint Integration**: Respects operational rules from day one

### ⚖️ Smart Optimization
- **Load Balancing**: Smooths daily variance while preserving requirements
- **Greedy Algorithm**: Transfers work from peak to valley days efficiently
- **Constraint Preservation**: Never breaks what forecasting established

### 💻 Professional Interface
- **Real-time Validation**: Immediate feedback on capacity and feasibility
- **Dynamic Gauges**: Visual capacity utilization as you enter requirements
- **Step-by-step Workflow**: Input → Forecast → Optimize → Results
- **Before/After Comparison**: See exactly what optimization achieved

## 📊 System Architecture

The system uses a **two-stage intelligent architecture**:

1. **Stage 1: Forecasting** - Rule-based assignment focusing on requirement satisfaction
2. **Stage 2: Optimization** - Load balancing focusing on resource efficiency

This separation ensures business needs are met while achieving optimal resource utilization.

For detailed technical documentation, see: **[📖 System Architecture & Methodology](docs/SYSTEM_ARCHITECTURE_AND_METHODOLOGY.md)**

## 📁 Project Structure

```
├── src/                          # Source code
│   ├── interface/                # Streamlit web application
│   ├── forecast/                 # Forecasting engine
│   ├── smooth/                   # Optimization engine
│   ├── etl/                      # Data processing pipeline
│   └── viz/                      # Visualization components
├── docs/                         # Documentation
│   ├── SYSTEM_ARCHITECTURE_AND_METHODOLOGY.md  # Complete technical guide
│   ├── DOCKER_DEPLOYMENT.md     # Docker deployment guide
│   ├── PLANNER_USER_GUIDE.md    # User instructions
│   ├── data_dictionary.md       # Data schema documentation
│   └── data_sample_list.md      # Sample data catalog
├── config/                       # Configuration files
│   └── personnel_intensive.yml  # Product categorization rules
├── data/                         # Data storage
│   ├── processed/                # Cleaned and normalized data
│   └── reports/                  # System analysis reports
├── logs/                         # Application logs
├── project-management/           # Project planning and notes
├── docker-compose.yml           # Docker deployment configuration
├── Dockerfile                   # Container definition
├── deploy.sh                    # Easy deployment script
└── requirements.txt             # Python dependencies
```

## 🎮 Usage Guide

### 1. Input Requirements
- **Products**: Enter product names, hours needed, priorities, and deadlines
- **Constraints**: Configure line availability and operational rules
- **Quick Demo**: Use "Load Sample Scenario" for immediate demonstration

### 2. Review Forecast
- See initial schedule based on historical data and requirements
- Check capacity utilization gauges
- Validate constraint compliance

### 3. Run Optimization
- Generate balanced load distribution
- View before/after comparison
- Review detailed transfer explanations

### 4. Analyze Results
- **Weekly Schedule**: Day-by-day line assignments
- **Optimization Impact**: Variance reduction and efficiency gains
- **Constraint Compliance**: Full validation report
- **Export Options**: Download schedule for production use

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[System Architecture & Methodology](docs/SYSTEM_ARCHITECTURE_AND_METHODOLOGY.md)** | Complete technical documentation with algorithms, data flows, and implementation details |
| **[Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)** | Production deployment instructions with nginx and monitoring |
| **[Planner User Guide](docs/PLANNER_USER_GUIDE.md)** | Step-by-step instructions for production planners |
| **[Data Dictionary](docs/data_dictionary.md)** | Data schema and field definitions |

## 🔧 Development

### Local Development Setup
```bash
# Activate environment
conda activate py310

# Install dependencies
pip install -r requirements.txt

# Run ETL pipeline (if needed)
python src/etl/ingest.py

# Start development server
streamlit run src/interface/planner_app.py --server.port 8501
```

### Docker Development
```bash
# Build development image
docker build -t ritter-sport-planner:dev .

# Run with code mounted for hot reload
docker run -p 8501:8501 \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/data:/app/data \
  ritter-sport-planner:dev
```

## 🎯 Success Metrics

### Technical Performance
- ✅ **Load Balancing**: >20% variance reduction achieved
- ✅ **Constraint Compliance**: 100% operational constraint satisfaction
- ✅ **Processing Speed**: <10 seconds for full forecast + optimization
- ✅ **Data Quality**: >90% historical data coverage with >90% line identification

### Business Impact
- **Planning Efficiency**: Reduced planning time from hours to minutes
- **Resource Optimization**: Better capacity utilization and balanced workloads
- **Employee Satisfaction**: More predictable and manageable work schedules
- **Cost Efficiency**: Optimized line utilization and reduced idle time

## 🚀 Future Roadmap

### Near-term (3 months)
- **Enhanced Forecasting**: Machine learning models (LightGBM, XGBoost)
- **Advanced Optimization**: Mixed Integer Linear Programming (MILP)
- **Extended Constraints**: Energy costs, maintenance scheduling

### Long-term (6-12 months)
- **Enterprise Integration**: ERP connectivity, real-time monitoring
- **Intelligent Planning**: Automatic requirement generation, predictive maintenance
- **Advanced Analytics**: Performance trends, scenario planning

## 🆘 Troubleshooting

### Common Issues

**Port 8501 already in use:**
```bash
# Find and kill the process
lsof -i :8501
kill <PID>
# Then restart: ./deploy.sh
```

**Docker build issues:**
```bash
# Clean build
docker compose build --no-cache
```

**Module import errors:**
```bash
# Ensure you're in the correct conda environment
conda activate py310
```

**Application logs:**
```bash
# View real-time logs
docker compose logs -f ritter-sport-planner
```

## 🤝 Support

For technical issues or questions:
1. Check the **[System Architecture & Methodology](docs/SYSTEM_ARCHITECTURE_AND_METHODOLOGY.md)** for detailed explanations
2. Review the **[Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)** for deployment issues
3. Consult the **[Planner User Guide](docs/PLANNER_USER_GUIDE.md)** for usage questions
4. Check application logs in the `logs/` directory

## 📝 License

This project is part of a Proof of Concept for Ritter Sport production optimization.

---

**Transform your production planning from guesswork to science** 🍫📊