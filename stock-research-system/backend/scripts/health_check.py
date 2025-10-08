#!/usr/bin/env python3
"""
System Health Check Script
Validates all components are working correctly
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()


class HealthChecker:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'overall_status': 'UNKNOWN'
        }

    def add_check(self, component: str, status: str, message: str, details: dict = None):
        """Add a health check result"""
        self.results['checks'].append({
            'component': component,
            'status': status,
            'message': message,
            'details': details or {}
        })

    async def check_environment(self):
        """Check environment variables"""
        print("\n🔍 Checking Environment Variables...")

        required = ['OPENAI_API_KEY', 'MONGODB_URL']
        optional = ['TAVILY_API_KEY', 'REDIS_URL']

        all_good = True
        for var in required:
            if os.getenv(var):
                self.add_check('Environment', 'PASS', f'{var} is set')
                print(f"   ✅ {var}")
            else:
                self.add_check('Environment', 'FAIL', f'{var} is missing')
                print(f"   ❌ {var} - REQUIRED")
                all_good = False

        for var in optional:
            if os.getenv(var):
                self.add_check('Environment', 'PASS', f'{var} is set')
                print(f"   ✅ {var}")
            else:
                self.add_check('Environment', 'WARN', f'{var} is not set (optional)')
                print(f"   ⚠️  {var} - OPTIONAL")

        return all_good

    async def check_mongodb(self):
        """Check MongoDB connection"""
        print("\n🔍 Checking MongoDB Connection...")

        try:
            from services.mongodb_connection import mongodb_connection

            await mongodb_connection.connect()
            db = mongodb_connection.get_database()

            # Test connection
            result = await db.command('ping')

            # Get collections
            collections = await db.list_collection_names()

            self.add_check('MongoDB', 'PASS', 'Connected successfully', {
                'collections': collections[:5],
                'total_collections': len(collections)
            })

            print(f"   ✅ MongoDB connected")
            print(f"   ✅ {len(collections)} collections available")

            await mongodb_connection.close()
            return True

        except Exception as e:
            self.add_check('MongoDB', 'FAIL', str(e))
            print(f"   ❌ MongoDB connection failed: {e}")
            return False

    async def check_redis(self):
        """Check Redis connection"""
        print("\n🔍 Checking Redis Connection...")

        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            self.add_check('Redis', 'SKIP', 'REDIS_URL not configured')
            print(f"   ⚠️  Redis not configured (optional)")
            return True

        try:
            from services.tavily_cache import get_tavily_cache

            cache = get_tavily_cache(redis_url)

            if cache.enabled:
                stats = await cache.get_stats()

                self.add_check('Redis', 'PASS', 'Connected successfully', {
                    'hit_rate': stats.get('hit_rate', 0),
                    'total_requests': stats.get('total_requests', 0)
                })

                print(f"   ✅ Redis connected")
                print(f"   ✅ Hit rate: {stats.get('hit_rate', 0)}%")

                await cache.close()
                return True
            else:
                self.add_check('Redis', 'WARN', 'Redis client created but not enabled')
                print(f"   ⚠️  Redis client disabled")
                return True

        except Exception as e:
            self.add_check('Redis', 'WARN', str(e))
            print(f"   ⚠️  Redis connection failed (non-critical): {e}")
            return True

    async def check_openai(self):
        """Check OpenAI API"""
        print("\n🔍 Checking OpenAI API...")

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.add_check('OpenAI', 'FAIL', 'API key not set')
            print(f"   ❌ OpenAI API key not set")
            return False

        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=api_key,
                temperature=0,
                max_tokens=10
            )

            # Test API call
            response = await llm.ainvoke("Say 'OK'")

            self.add_check('OpenAI', 'PASS', 'API key valid', {
                'response': response.content[:50]
            })

            print(f"   ✅ OpenAI API key valid")
            print(f"   ✅ Test call successful")

            return True

        except Exception as e:
            self.add_check('OpenAI', 'FAIL', str(e))
            print(f"   ❌ OpenAI API test failed: {e}")
            return False

    async def check_tavily(self):
        """Check Tavily API"""
        print("\n🔍 Checking Tavily API...")

        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            self.add_check('Tavily', 'SKIP', 'API key not set (optional)')
            print(f"   ⚠️  Tavily API key not set (optional)")
            return True

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)

            # Test search
            result = await asyncio.to_thread(
                client.search,
                query="test",
                max_results=1
            )

            self.add_check('Tavily', 'PASS', 'API key valid', {
                'results_count': len(result.get('results', []))
            })

            print(f"   ✅ Tavily API key valid")
            print(f"   ✅ Test search successful")

            return True

        except Exception as e:
            self.add_check('Tavily', 'WARN', str(e))
            print(f"   ⚠️  Tavily API test failed (non-critical): {e}")
            return True

    async def check_workflow(self):
        """Check workflow initialization"""
        print("\n🔍 Checking Workflow Initialization...")

        try:
            from langchain_openai import ChatOpenAI
            from workflow.enhanced_stock_workflow import EnhancedStockWorkflow
            from services.mongodb_connection import mongodb_connection

            # Connect to DB
            await mongodb_connection.connect()
            db = mongodb_connection.get_database()

            llm = ChatOpenAI(
                model="gpt-4",
                api_key=os.getenv('OPENAI_API_KEY'),
                temperature=0.2
            )

            workflow = EnhancedStockWorkflow(
                llm=llm,
                database=db,
                tavily_api_key=os.getenv('TAVILY_API_KEY'),
                redis_url=os.getenv('REDIS_URL')
            )

            details = {
                'base_agents': 4,
                'tavily_enabled': workflow.hybrid_orchestrator is not None,
                'cache_enabled': workflow.tavily_cache is not None,
                'router_enabled': workflow.smart_router is not None
            }

            self.add_check('Workflow', 'PASS', 'Initialized successfully', details)

            print(f"   ✅ Workflow initialized")
            print(f"   ✅ Base agents: 4")
            print(f"   ✅ Tavily enrichment: {'enabled' if details['tavily_enabled'] else 'disabled'}")
            print(f"   ✅ Redis caching: {'enabled' if details['cache_enabled'] else 'disabled'}")
            print(f"   ✅ Smart routing: {'enabled' if details['router_enabled'] else 'disabled'}")

            await mongodb_connection.close()
            return True

        except Exception as e:
            self.add_check('Workflow', 'FAIL', str(e))
            print(f"   ❌ Workflow initialization failed: {e}")
            return False

    async def run_all_checks(self):
        """Run all health checks"""
        print("="*60)
        print("SYSTEM HEALTH CHECK")
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run checks
        checks = [
            await self.check_environment(),
            await self.check_mongodb(),
            await self.check_redis(),
            await self.check_openai(),
            await self.check_tavily(),
            await self.check_workflow()
        ]

        # Determine overall status
        failed_checks = [c for c in self.results['checks'] if c['status'] == 'FAIL']
        warn_checks = [c for c in self.results['checks'] if c['status'] == 'WARN']

        if failed_checks:
            self.results['overall_status'] = 'FAILED'
            status_icon = '❌'
            status_text = 'FAILED'
        elif warn_checks:
            self.results['overall_status'] = 'WARNING'
            status_icon = '⚠️'
            status_text = 'WARNING'
        else:
            self.results['overall_status'] = 'HEALTHY'
            status_icon = '✅'
            status_text = 'HEALTHY'

        # Print summary
        print("\n" + "="*60)
        print(f"{status_icon} OVERALL STATUS: {status_text}")
        print("="*60)

        print(f"\nSummary:")
        print(f"  • Total checks: {len(self.results['checks'])}")
        print(f"  • Passed: {len([c for c in self.results['checks'] if c['status'] == 'PASS'])}")
        print(f"  • Failed: {len(failed_checks)}")
        print(f"  • Warnings: {len(warn_checks)}")
        print(f"  • Skipped: {len([c for c in self.results['checks'] if c['status'] == 'SKIP'])}")

        if failed_checks:
            print(f"\n❌ Failed Checks:")
            for check in failed_checks:
                print(f"  • {check['component']}: {check['message']}")

        if warn_checks:
            print(f"\n⚠️  Warnings:")
            for check in warn_checks:
                print(f"  • {check['component']}: {check['message']}")

        print()

        return self.results['overall_status'] == 'HEALTHY'

    def save_report(self, filename='health_check_report.json'):
        """Save health check report to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📄 Health check report saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save report: {e}")


async def main():
    checker = HealthChecker()

    is_healthy = await checker.run_all_checks()

    # Save report
    checker.save_report()

    # Exit with appropriate code
    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    asyncio.run(main())
