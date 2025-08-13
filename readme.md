# Ritter Sport Production Load Balancing Decision Support Tool

> **Transform manual production planning into data-driven optimization**

A Proof of Concept decision support system that helps production planners at Ritter Sport optimize weekly load distribution across 5 production lines, replacing educated guesses with statistical forecasting and constraint-aware optimization.

## 🎯 The Problem

**Current State**: Production planners manually create weekly schedules based on manager requirements, leading to:
- Suboptimal load distribution (heavy Mon-Wed, light Thu-Fri)
- Overtime costs and employee stress
- Underutilized equipment and inefficient resource allocation
- Planning decisions based on experience rather than data

**Root Issue**: Managers define production demands for 1-2 weeks ahead, but the planner lacks tools to systematically forecast workload and optimize distribution across constraints.


## 🚀 The Solution

### What We're Building
A decision support tool that transforms the planning process:

**Input** → **Process** → **Output**
```
Manager Requirements    →    Forecast & Optimize    →    Optimized Weekly Plan
+ Constraints          →    (Data-Driven)          →    + Load Distribution
+ Other Factors        →                           →    + Constraint Compliance
```

### Core Capabilities
1. **📊 Intelligent Forecasting**: Historical data + Ritter Sport domain insights → predicted load patterns
2. **⚖️ Constraint-Aware Optimization**: Balance load across Mon-Fri and 5 lines while respecting operational rules
3. **🎯 Planner-Friendly Interface**: Clear inputs, transparent reasoning, actionable outputs

### Expected Benefits
- **Cost Efficiency**: ~20% reduction in overtime hours, ~15% less idle time
- **Employee Satisfaction**: More manageable, predictable work schedules
- **Resource Optimization**: Better equipment utilization across the week
- **Decision Quality**: Data-driven planning replaces manual guesswork


## 📋 Implementation Plan

### Phase 1: Foundation (Days 1-4)
- **✅ Data Ingestion**: Parse historical Excel files, normalize schema
- **✅ ETL Pipeline**: Clean, validate, and structure production data
- **📊 Baseline Analysis**: Understand current patterns and constraints

### Phase 2: Core Intelligence (Days 5-8)
- **🧠 Forecasting Model**: Build statistical model for load prediction
- **⚙️ Optimization Engine**: Implement constraint-aware scheduling algorithm
- **🔧 Integration**: Connect forecasting → optimization pipeline

### Phase 3: User Interface (Days 9-12)
- **📱 Planner Interface**: Input forms for requirements and constraints
- **📈 Visualization**: Clear schedule outputs and load distribution charts
- **🎯 Demo Preparation**: End-to-end workflow demonstration

### Phase 4: Validation & Polish (Days 13-14)
- **🧪 Testing**: Validate against historical scenarios
- **📖 Documentation**: User guides and technical documentation
- **🎤 Presentation**: Stakeholder demo and feedback collection


## 🏭 Production Context

### Lines & Constraints
- **5 Production Lines**: hohl2, hohl3, hohl4, massiv2, massiv3
- **3 Shifts/Day**: 24-hour operation with mandatory idle time
- **Key Constraints**:
  - At least one line idle per day
  - No simultaneous personnel-intensive sorts
  - Prefer not to split sort blocks on Hohl lines
  - Avoid same sort on consecutive days

### Historical Patterns
- **Current Load Distribution**: Heavy Mon-Wed (~280h peak), light Thu-Fri (~37h minimum)
- **Line Utilization**: massiv3 and hohl3 bear highest loads, hohl4 underutilized
- **Improvement Opportunity**: Smooth distribution could reduce peaks by 20%


## 🛠️ Technical Stack

### Core Technologies
- **Backend**: Python (data processing, ML models)
- **Forecasting**: LightGBM/XGBoost for statistical modeling
- **Optimization**: OR-Tools for constraint programming
- **Frontend**: Streamlit/Dash for planner interface
- **Data**: Excel/CSV input → normalized PostgreSQL/SQLite

### Key Libraries
- `pandas`, `numpy` for data manipulation
- `scikit-learn`, `lightgbm` for forecasting
- `ortools` for optimization
- `streamlit` for user interface
- `plotly` for visualization


## 📁 Project Structure

```
anlage_data/
├── README.md                    # This file
├── .cursorrules                 # Project rules and constraints
├── src/
│   ├── etl/                     # Data ingestion and normalization
│   ├── forecast/                # Load forecasting models
│   ├── smooth/                  # Optimization algorithms
│   └── viz/                     # User interface and charts
├── data/
│   ├── processed/               # Normalized data outputs
│   └── reports/                 # Analysis and validation reports
├── config/
│   └── personnel_intensive.yml  # Business constraint definitions
├── planning/                    # Project plans and specifications
├── tasks/                       # Implementation checklists
└── logs/                        # System operation logs
```


## 🚦 Getting Started

### Quick Start with Docker (Recommended)
1. **Clone the repository**
2. **Install Docker and Docker Compose**
3. **Run**: `./deploy.sh` or `docker compose up --build`
4. **Open**: http://localhost:8501 in your browser
5. **Demo**: Use "Load Sample Scenario" to see the system in action

### For Developers
1. **Explore the Data**: Check `data/processed/normalized_daily.csv` for current data structure
2. **Review Constraints**: Read `config/personnel_intensive.yml` and `.cursorrules`
3. **Follow the Plan**: Check `planning/POC_PLAN.md` for detailed implementation steps
4. **Track Progress**: Update `tasks/section1_checklist.md` as you complete tasks

### For Planners
1. **Open the Tool**: Launch the web interface (Docker or local installation)
2. **Input Requirements**: Enter production demands from management meetings
3. **Review Forecast**: See predicted load distribution based on historical data
4. **Optimize Schedule**: Get constraint-compliant weekly plan with load balancing
5. **Export Results**: Download schedule for production implementation

### Docker Deployment
See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed deployment instructions, including production setup with nginx and monitoring configurations.


## 🎯 Success Metrics

### Technical Validation
- ✅ Data ingestion: 90%+ rows successfully normalized
- 🎯 Forecast accuracy: <15% MAPE on historical validation
- ⚖️ Constraint compliance: 100% adherence to operational rules
- 🚀 Performance: <30 seconds forecast-to-schedule generation

### Business Impact
- 📊 Load Distribution: Reduced weekday variance by 15%+
- ⏰ Overtime Reduction: 20% fewer overtime hours
- 😊 Planner Satisfaction: Improved decision confidence
- 🔧 Adoption: Successfully integrated into weekly planning process

## 📞 Contact & Support

- **Project Lead**: Planning & AI Team
- **Technical Issues**: Check `logs/` directory or create GitHub issue
- **Business Questions**: Refer to `planning/POC_PLAN.md`
- **Last Updated**: 2025-01-11

---

*This is a Proof of Concept focused on demonstrating value through minimal viable features. Full production deployment will require additional security, scalability, and integration considerations.*
