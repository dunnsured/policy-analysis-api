"""
Supabase client for storing policy analysis results
"""

import logging
from typing import Dict, Any, Optional
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
      """Service for interacting with Supabase database"""

    def __init__(self):
              self.client: Optional[Client] = None
              if settings.SUPABASE_URL and settings.SUPABASE_KEY:
                            try:
                                              self.client = create_client(
                                                                    settings.SUPABASE_URL,
                                                                    settings.SUPABASE_KEY
                                                                )
                                              logger.info("✅ Supabase client initialized")
                                          except Exception as e:
                                                            logger.error(f"❌ Failed to initialize Supabase client: {e}")
                                                    else:
            logger.warning("⚠️  Supabase credentials not configured")


    async def store_analysis_result(
              self,
              policy_id: str,
              analysis_id: str,
              analysis_data: Dict[str, Any],
              status: str = "completed"
          ) -> bool:
                    """
                            Store policy analysis results in Supabase.
                                    This updates the policy record with analysis results.
                                            """
                    if not self.client:
                                  logger.warning("Supabase client not initialized, skipping storage")
                                  return False

                    try:
                                  # Update the policies table with analysis results
                                  result = self.client.table("policies").update({
                                                    "analysis_id": analysis_id,
                                                    "analysis_status": status,
                                                    "analysis_result": analysis_data,
                                                    "analyzed_at": "now()"
                                                }).eq("id", policy_id).execute()

                        logger.info(f"✅ Stored analysis results for policy {policy_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to store analysis result: {e}")
            return False


# Create a singleton instance
supabase_service = SupabaseService()
