#!/usr/bin/env python3
"""Test MongoDB connection"""

import os
import sys
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        # Get MongoDB URL from environment
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("❌ MONGODB_URL not found in environment variables")
            return False

        print(f"📡 Connecting to MongoDB...")
        print(f"   URL: {mongodb_url[:30]}...")  # Show first 30 chars for security

        # Create a new client and connect to the server
        client = MongoClient(
            mongodb_url,
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )

        # Test the connection
        print("🔍 Testing connection...")
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")

        # List databases
        print("\n📚 Available databases:")
        for db_name in client.list_database_names():
            print(f"   - {db_name}")

        # Test stock_research database
        db = client['stock_research']
        print(f"\n📊 Collections in 'stock_research' database:")
        for collection_name in db.list_collection_names():
            count = db[collection_name].count_documents({})
            print(f"   - {collection_name}: {count} documents")

        # Close connection
        client.close()
        return True

    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print(f"\n🔧 Troubleshooting tips:")
        print("   1. Check your internet connection")
        print("   2. Verify MongoDB Atlas cluster is running")
        print("   3. Check IP whitelist in MongoDB Atlas")
        print("   4. Verify credentials in .env file")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("MongoDB Connection Test")
    print("=" * 50)

    success = test_mongodb_connection()
    sys.exit(0 if success else 1)