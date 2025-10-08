"""MongoDB Index Optimization for Stock Research System"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MongoDBIndexManager:
    """Manages MongoDB indexes for optimal performance"""

    def __init__(self, connection_uri: str = None):
        """Initialize index manager

        Args:
            connection_uri: MongoDB connection URI
        """
        self.connection_uri = connection_uri or os.getenv('MONGODB_URI')
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_uri)
            self.db = self.client.stock_research_prod
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB Atlas")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def create_indexes(self):
        """Create all required indexes for optimal performance"""

        index_definitions = {
            'analyses': [
                # Primary indexes
                {
                    'keys': [('user_id', 1), ('created_at', -1)],
                    'name': 'user_recent_analyses',
                    'background': True
                },
                {
                    'keys': [('request_id', 1)],
                    'name': 'request_lookup',
                    'unique': True,
                    'background': True
                },
                {
                    'keys': [('symbols', 1), ('created_at', -1)],
                    'name': 'symbol_analyses',
                    'background': True
                },
                {
                    'keys': [('status', 1), ('created_at', -1)],
                    'name': 'status_filter',
                    'background': True
                },
                # Text search index
                {
                    'keys': [('query', 'text'), ('response', 'text')],
                    'name': 'text_search',
                    'background': True
                },
                # TTL index for auto-cleanup
                {
                    'keys': [('expires_at', 1)],
                    'name': 'ttl_cleanup',
                    'expireAfterSeconds': 0,
                    'background': True
                }
            ],

            'analysis_results': [
                {
                    'keys': [('analysis_id', 1), ('agent_type', 1)],
                    'name': 'analysis_agent_results',
                    'background': True
                },
                {
                    'keys': [('created_at', -1)],
                    'name': 'recent_results',
                    'background': True
                },
                {
                    'keys': [('symbols', 1), ('agent_type', 1), ('created_at', -1)],
                    'name': 'symbol_agent_results',
                    'background': True
                }
            ],

            'notifications': [
                {
                    'keys': [('user_id', 1), ('read', 1), ('created_at', -1)],
                    'name': 'user_unread_notifications',
                    'background': True
                },
                {
                    'keys': [('expires_at', 1)],
                    'name': 'notification_ttl',
                    'expireAfterSeconds': 2592000,  # 30 days
                    'background': True
                }
            ],

            'cache_entries': [
                {
                    'keys': [('cache_key', 1)],
                    'name': 'cache_key_lookup',
                    'unique': True,
                    'background': True
                },
                {
                    'keys': [('expires_at', 1)],
                    'name': 'cache_ttl',
                    'expireAfterSeconds': 0,
                    'background': True
                }
            ],

            'user_sessions': [
                {
                    'keys': [('session_id', 1)],
                    'name': 'session_lookup',
                    'unique': True,
                    'background': True
                },
                {
                    'keys': [('user_id', 1), ('active', 1)],
                    'name': 'user_active_sessions',
                    'background': True
                },
                {
                    'keys': [('expires_at', 1)],
                    'name': 'session_ttl',
                    'expireAfterSeconds': 0,
                    'background': True
                }
            ],

            'audit_logs': [
                {
                    'keys': [('user_id', 1), ('action', 1), ('timestamp', -1)],
                    'name': 'user_action_audit',
                    'background': True
                },
                {
                    'keys': [('timestamp', -1)],
                    'name': 'recent_audit',
                    'background': True
                },
                {
                    'keys': [('expires_at', 1)],
                    'name': 'audit_ttl',
                    'expireAfterSeconds': 7776000,  # 90 days
                    'background': True
                }
            ]
        }

        results = []

        for collection_name, indexes in index_definitions.items():
            collection = self.db[collection_name]

            for index_def in indexes:
                try:
                    keys = index_def.pop('keys')

                    # Check if index exists
                    existing_indexes = await collection.list_indexes().to_list(None)
                    index_exists = any(
                        idx.get('name') == index_def.get('name')
                        for idx in existing_indexes
                    )

                    if not index_exists:
                        result = await collection.create_index(keys, **index_def)
                        logger.info(f"Created index {result} on {collection_name}")
                        results.append({
                            'collection': collection_name,
                            'index': result,
                            'status': 'created'
                        })
                    else:
                        logger.info(f"Index {index_def.get('name')} already exists on {collection_name}")
                        results.append({
                            'collection': collection_name,
                            'index': index_def.get('name'),
                            'status': 'exists'
                        })

                except Exception as e:
                    logger.error(f"Failed to create index on {collection_name}: {e}")
                    results.append({
                        'collection': collection_name,
                        'index': index_def.get('name'),
                        'status': 'failed',
                        'error': str(e)
                    })

        return results

    async def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze current index usage and performance"""

        usage_stats = {}

        collections = ['analyses', 'analysis_results', 'notifications', 'cache_entries']

        for collection_name in collections:
            collection = self.db[collection_name]

            try:
                # Get index stats
                stats = await collection.aggregate([
                    {'$indexStats': {}}
                ]).to_list(None)

                # Get collection stats
                coll_stats = await self.db.command('collStats', collection_name)

                usage_stats[collection_name] = {
                    'document_count': coll_stats.get('count', 0),
                    'size_bytes': coll_stats.get('size', 0),
                    'avg_doc_size': coll_stats.get('avgObjSize', 0),
                    'index_count': len(stats),
                    'indexes': []
                }

                for idx_stat in stats:
                    usage_stats[collection_name]['indexes'].append({
                        'name': idx_stat.get('name'),
                        'accesses': idx_stat.get('accesses', {}).get('ops', 0),
                        'since': idx_stat.get('accesses', {}).get('since', ''),
                        'host': idx_stat.get('host')
                    })

            except Exception as e:
                logger.error(f"Failed to analyze {collection_name}: {e}")
                usage_stats[collection_name] = {'error': str(e)}

        return usage_stats

    async def optimize_indexes(self) -> List[Dict[str, Any]]:
        """Optimize indexes based on usage patterns"""

        optimizations = []

        # Analyze current usage
        usage_stats = await self.analyze_index_usage()

        for collection_name, stats in usage_stats.items():
            if 'error' in stats:
                continue

            collection = self.db[collection_name]

            # Find unused indexes (0 accesses)
            unused_indexes = [
                idx for idx in stats.get('indexes', [])
                if idx['accesses'] == 0 and idx['name'] != '_id_'
            ]

            # Drop unused indexes
            for idx in unused_indexes:
                try:
                    await collection.drop_index(idx['name'])
                    logger.info(f"Dropped unused index {idx['name']} on {collection_name}")
                    optimizations.append({
                        'action': 'drop',
                        'collection': collection_name,
                        'index': idx['name'],
                        'reason': 'unused'
                    })
                except Exception as e:
                    logger.error(f"Failed to drop index {idx['name']}: {e}")

            # Rebuild fragmented indexes (high document count collections)
            if stats['document_count'] > 100000:
                try:
                    await collection.reindex()
                    logger.info(f"Reindexed {collection_name}")
                    optimizations.append({
                        'action': 'reindex',
                        'collection': collection_name,
                        'reason': 'high_document_count'
                    })
                except Exception as e:
                    logger.error(f"Failed to reindex {collection_name}: {e}")

        return optimizations

    async def create_compound_indexes(self) -> List[str]:
        """Create compound indexes for complex queries"""

        compound_indexes = [
            {
                'collection': 'analyses',
                'index': [
                    ('user_id', 1),
                    ('symbols', 1),
                    ('status', 1),
                    ('created_at', -1)
                ],
                'name': 'user_symbol_status_compound',
                'background': True
            },
            {
                'collection': 'analysis_results',
                'index': [
                    ('analysis_id', 1),
                    ('agent_type', 1),
                    ('confidence_score', -1)
                ],
                'name': 'analysis_agent_confidence_compound',
                'background': True
            }
        ]

        created = []

        for idx_def in compound_indexes:
            collection = self.db[idx_def['collection']]

            try:
                result = await collection.create_index(
                    idx_def['index'],
                    name=idx_def['name'],
                    background=idx_def['background']
                )
                created.append(result)
                logger.info(f"Created compound index {result}")
            except Exception as e:
                if 'already exists' not in str(e):
                    logger.error(f"Failed to create compound index: {e}")

        return created

    async def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow running queries for optimization"""

        try:
            # Get slow query log from system.profile
            slow_queries = await self.db.system.profile.find({
                'millis': {'$gt': 100}  # Queries taking more than 100ms
            }).sort('ts', -1).limit(20).to_list(None)

            formatted_queries = []
            for query in slow_queries:
                formatted_queries.append({
                    'timestamp': query.get('ts'),
                    'duration_ms': query.get('millis'),
                    'collection': query.get('ns', '').split('.')[-1],
                    'operation': query.get('op'),
                    'query': query.get('command', {}).get('filter', {}),
                    'docs_examined': query.get('docsExamined', 0),
                    'keys_examined': query.get('keysExamined', 0)
                })

            return formatted_queries

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    async def enable_profiling(self, level: int = 1, slow_ms: int = 100):
        """Enable query profiling

        Args:
            level: 0=off, 1=slow queries only, 2=all queries
            slow_ms: Threshold for slow queries (milliseconds)
        """
        try:
            result = await self.db.command(
                'profile',
                level,
                slowms=slow_ms
            )
            logger.info(f"Profiling set to level {level} with threshold {slow_ms}ms")
            return result
        except Exception as e:
            logger.error(f"Failed to enable profiling: {e}")
            return None


async def optimize_mongodb_indexes():
    """Main function to optimize MongoDB indexes"""

    manager = MongoDBIndexManager()

    try:
        # Connect to MongoDB
        await manager.connect()

        # Create indexes
        print("\n=== Creating Indexes ===")
        created = await manager.create_indexes()
        for result in created:
            print(f"  {result['collection']}: {result['index']} - {result['status']}")

        # Create compound indexes
        print("\n=== Creating Compound Indexes ===")
        compound = await manager.create_compound_indexes()
        for idx in compound:
            print(f"  Created: {idx}")

        # Analyze usage
        print("\n=== Index Usage Analysis ===")
        usage = await manager.analyze_index_usage()
        for coll, stats in usage.items():
            if 'error' not in stats:
                print(f"\n  {coll}:")
                print(f"    Documents: {stats['document_count']:,}")
                print(f"    Size: {stats['size_bytes'] / 1024 / 1024:.2f} MB")
                print(f"    Indexes: {stats['index_count']}")

        # Optimize indexes
        print("\n=== Index Optimization ===")
        optimizations = await manager.optimize_indexes()
        for opt in optimizations:
            print(f"  {opt['action']}: {opt.get('collection')} - {opt.get('index', '')} ({opt['reason']})")

        # Enable profiling for monitoring
        await manager.enable_profiling(level=1, slow_ms=100)
        print("\n✅ MongoDB optimization complete!")

    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")

    finally:
        if manager.client:
            manager.client.close()


if __name__ == "__main__":
    asyncio.run(optimize_mongodb_indexes())