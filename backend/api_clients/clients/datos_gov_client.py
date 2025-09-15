"""
Datos.gov.co API Client
Access Colombian open data through the CKAN-based datos.gov.co platform
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from api_clients.base.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class DatosGovClient(BaseAPIClient):
    """
    Client for datos.gov.co CKAN API
    Provides access to Colombian open government datasets
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize datos.gov.co client"""
        default_config = {
            'base_url': 'https://www.datos.gov.co/api',
            'api_key': None,  # API key optional for public data
            'cache_ttl': 3600,  # 1 hour cache for datasets
            'rate_limit': 100
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # CKAN API endpoints
        self.endpoints = {
            'package_list': 'action/package_list',  # List all datasets
            'package_show': 'action/package_show',  # Get dataset details
            'package_search': 'action/package_search',  # Search datasets
            'resource_show': 'action/resource_show',  # Get resource details
            'group_list': 'action/group_list',  # List organizations/groups
            'tag_list': 'action/tag_list',  # List all tags
            'organization_list': 'action/organization_list',  # List organizations
            'organization_show': 'action/organization_show',  # Get organization details
            'status_show': 'action/status_show',  # API status
            'site_read': 'action/site_read'  # Site permissions
        }

        # Common search filters
        self.common_tags = [
            'economia', 'educacion', 'salud', 'transporte', 'medio-ambiente',
            'seguridad', 'justicia', 'hacienda', 'presupuesto', 'demografía',
            'comercio', 'industria', 'agricultura', 'mineria', 'energia'
        ]

        # Data quality thresholds
        self.quality_thresholds = {
            'min_resources': 1,
            'max_age_days': 365,  # Data older than 1 year flagged
            'min_description_length': 50
        }

    async def search_datasets(
        self,
        query: str = '',
        organization: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start: int = 0,
        rows: int = 100,
        sort: str = 'score desc, metadata_modified desc'
    ) -> Dict:
        """
        Search datasets using CKAN search API

        Args:
            query: Search query string
            organization: Filter by organization name
            tags: List of tags to filter by
            start: Start index for pagination
            rows: Number of rows to return (max 1000)
            sort: Sort order

        Returns:
            Search results with metadata
        """
        params = {
            'q': query,
            'start': start,
            'rows': min(rows, 1000),  # CKAN limit
            'sort': sort
        }

        # Add filters
        fq_filters = []
        if organization:
            fq_filters.append(f'organization:{organization}')

        if tags:
            for tag in tags:
                fq_filters.append(f'tags:{tag}')

        if fq_filters:
            params['fq'] = ' AND '.join(fq_filters)

        data = await self.fetch_data(self.endpoints['package_search'], params)

        # Add search metadata
        if 'result' in data:
            data['search_metadata'] = {
                'query': query,
                'total_results': data['result'].get('count', 0),
                'start': start,
                'rows': rows,
                'has_more': (start + rows) < data['result'].get('count', 0)
            }

            # Enhance each dataset with quality score
            if 'results' in data['result']:
                for dataset in data['result']['results']:
                    dataset['quality_score'] = self._calculate_quality_score(dataset)

        return data

    async def get_dataset(
        self,
        dataset_id: str,
        include_resources: bool = True
    ) -> Dict:
        """
        Get detailed information about a specific dataset

        Args:
            dataset_id: Dataset identifier (name or ID)
            include_resources: Include resource details

        Returns:
            Dataset details with resources
        """
        params = {'id': dataset_id}

        data = await self.fetch_data(self.endpoints['package_show'], params)

        if 'result' in data and include_resources:
            # Enhance resource information
            dataset = data['result']
            if 'resources' in dataset:
                for resource in dataset['resources']:
                    resource['download_info'] = await self._analyze_resource(resource)

            # Add dataset analytics
            data['analytics'] = {
                'resource_count': len(dataset.get('resources', [])),
                'total_size': self._calculate_total_size(dataset.get('resources', [])),
                'last_updated': dataset.get('metadata_modified'),
                'data_freshness': self._assess_data_freshness(dataset.get('metadata_modified')),
                'quality_score': self._calculate_quality_score(dataset)
            }

        return data

    async def get_dataset_resources(
        self,
        dataset_id: str,
        resource_format: Optional[str] = None
    ) -> Dict:
        """
        Get resources for a specific dataset

        Args:
            dataset_id: Dataset identifier
            resource_format: Filter by format (CSV, JSON, XML, etc.)

        Returns:
            List of resources with download information
        """
        dataset_data = await self.get_dataset(dataset_id)

        if 'result' not in dataset_data:
            return {'error': 'Dataset not found', 'resources': []}

        resources = dataset_data['result'].get('resources', [])

        # Filter by format if specified
        if resource_format:
            resources = [
                r for r in resources
                if r.get('format', '').upper() == resource_format.upper()
            ]

        # Add download analysis for each resource
        enhanced_resources = []
        for resource in resources:
            enhanced_resource = resource.copy()
            enhanced_resource['download_analysis'] = await self._analyze_resource(resource)
            enhanced_resources.append(enhanced_resource)

        return {
            'dataset_id': dataset_id,
            'resources': enhanced_resources,
            'summary': {
                'total_resources': len(enhanced_resources),
                'formats': list(set(r.get('format', 'unknown') for r in enhanced_resources)),
                'total_size': self._calculate_total_size(enhanced_resources)
            }
        }

    async def list_organizations(self) -> Dict:
        """
        List all organizations in the portal

        Returns:
            List of organizations with metadata
        """
        data = await self.fetch_data(self.endpoints['organization_list'], {'all_fields': True})

        if 'result' in data:
            # Sort by dataset count
            organizations = sorted(
                data['result'],
                key=lambda x: x.get('package_count', 0),
                reverse=True
            )

            data['result'] = organizations
            data['summary'] = {
                'total_organizations': len(organizations),
                'total_datasets': sum(org.get('package_count', 0) for org in organizations),
                'most_active': organizations[0]['name'] if organizations else None
            }

        return data

    async def get_organization_datasets(
        self,
        organization_name: str,
        limit: int = 50
    ) -> Dict:
        """
        Get all datasets from a specific organization

        Args:
            organization_name: Organization identifier
            limit: Maximum number of datasets to return

        Returns:
            Organization datasets with summary
        """
        # First get organization details
        org_data = await self.fetch_data(
            self.endpoints['organization_show'],
            {'id': organization_name, 'include_datasets': True}
        )

        if 'result' not in org_data:
            return {'error': 'Organization not found'}

        organization = org_data['result']
        datasets = organization.get('packages', [])[:limit]

        # Calculate organization statistics
        stats = {
            'total_datasets': len(datasets),
            'data_formats': {},
            'update_frequency': {},
            'resource_count': 0
        }

        for dataset in datasets:
            # Count resources
            stats['resource_count'] += len(dataset.get('resources', []))

            # Count formats
            for resource in dataset.get('resources', []):
                fmt = resource.get('format', 'unknown')
                stats['data_formats'][fmt] = stats['data_formats'].get(fmt, 0) + 1

        return {
            'organization': {
                'name': organization.get('name'),
                'title': organization.get('title'),
                'description': organization.get('description'),
                'created': organization.get('created'),
                'package_count': organization.get('package_count')
            },
            'datasets': datasets,
            'statistics': stats
        }

    async def get_popular_datasets(
        self,
        limit: int = 20,
        category: Optional[str] = None
    ) -> Dict:
        """
        Get most popular/downloaded datasets

        Args:
            limit: Number of datasets to return
            category: Filter by category/tag

        Returns:
            Popular datasets with metrics
        """
        search_params = {
            'sort': 'views_recent desc',
            'rows': limit
        }

        if category:
            search_params['fq'] = f'tags:{category}'

        data = await self.search_datasets(**search_params)

        if 'result' in data and 'results' in data['result']:
            # Add popularity metrics
            for dataset in data['result']['results']:
                dataset['popularity_metrics'] = {
                    'views_recent': dataset.get('tracking_summary', {}).get('recent', 0),
                    'views_total': dataset.get('tracking_summary', {}).get('total', 0),
                    'resource_downloads': sum(
                        r.get('tracking_summary', {}).get('total', 0)
                        for r in dataset.get('resources', [])
                    )
                }

        return data

    async def download_resource(
        self,
        resource_id: str,
        save_path: Optional[str] = None
    ) -> Dict:
        """
        Download a resource file

        Args:
            resource_id: Resource identifier
            save_path: Local path to save file (optional)

        Returns:
            Download information and content
        """
        # Get resource details first
        resource_data = await self.fetch_data(
            self.endpoints['resource_show'],
            {'id': resource_id}
        )

        if 'result' not in resource_data:
            return {'error': 'Resource not found'}

        resource = resource_data['result']
        download_url = resource.get('url')

        if not download_url:
            return {'error': 'No download URL available'}

        try:
            # Download the actual data
            data = await self._make_request('GET', download_url.replace(self.base_url + '/', ''))

            download_info = {
                'resource_id': resource_id,
                'name': resource.get('name'),
                'format': resource.get('format'),
                'size': resource.get('size'),
                'download_url': download_url,
                'content': data,
                'downloaded_at': datetime.utcnow().isoformat()
            }

            # Save to file if path provided
            if save_path and 'raw_data' in data:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(data['raw_data'])
                download_info['saved_to'] = save_path

            return download_info

        except Exception as e:
            logger.error(f"Download failed for resource {resource_id}: {e}")
            return {'error': f'Download failed: {str(e)}'}

    async def get_api_status(self) -> Dict:
        """
        Check API health and status

        Returns:
            API status information
        """
        try:
            status_data = await self.fetch_data(self.endpoints['status_show'])

            return {
                'status': 'healthy',
                'api': 'datos.gov.co',
                'ckan_version': status_data.get('result', {}).get('ckan_version'),
                'extensions': status_data.get('result', {}).get('extensions', []),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'api': 'datos.gov.co',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def transform_response(self, response: Dict) -> Dict:
        """
        Transform datos.gov.co CKAN API response to standard format

        Args:
            response: Raw API response

        Returns:
            Transformed data
        """
        # CKAN responses have standard structure
        transformed = {
            'source': 'datos.gov.co',
            'success': response.get('success', False),
            'extracted_at': datetime.utcnow().isoformat()
        }

        # Include the result data
        if 'result' in response:
            transformed['result'] = response['result']

        # Include any error information
        if 'error' in response:
            transformed['error'] = response['error']

        # Add CKAN-specific metadata
        if 'help' in response:
            transformed['api_help'] = response['help']

        return transformed

    def _calculate_quality_score(self, dataset: Dict) -> float:
        """
        Calculate a quality score for a dataset

        Args:
            dataset: Dataset metadata

        Returns:
            Quality score (0-100)
        """
        score = 0.0

        # Has description (20 points)
        description = dataset.get('notes', '')
        if len(description) >= self.quality_thresholds['min_description_length']:
            score += 20
        elif description:
            score += 10

        # Has resources (30 points)
        resources = dataset.get('resources', [])
        if len(resources) >= self.quality_thresholds['min_resources']:
            score += 30

        # Data freshness (20 points)
        last_modified = dataset.get('metadata_modified')
        if last_modified:
            try:
                modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                days_old = (datetime.utcnow().replace(tzinfo=modified_date.tzinfo) - modified_date).days

                if days_old <= 30:
                    score += 20
                elif days_old <= 90:
                    score += 15
                elif days_old <= 365:
                    score += 10
            except:
                pass

        # Has tags (10 points)
        tags = dataset.get('tags', [])
        if len(tags) >= 3:
            score += 10
        elif tags:
            score += 5

        # Has license (10 points)
        license_id = dataset.get('license_id')
        if license_id and license_id != 'notspecified':
            score += 10

        # Resource formats (10 points)
        formats = set(r.get('format', '').upper() for r in resources)
        machine_readable = {'CSV', 'JSON', 'XML', 'XLS', 'XLSX', 'API'}
        if formats.intersection(machine_readable):
            score += 10

        return min(score, 100.0)

    def _assess_data_freshness(self, last_modified: Optional[str]) -> str:
        """Assess how fresh the data is"""
        if not last_modified:
            return 'unknown'

        try:
            modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            days_old = (datetime.utcnow().replace(tzinfo=modified_date.tzinfo) - modified_date).days

            if days_old <= 7:
                return 'very_fresh'
            elif days_old <= 30:
                return 'fresh'
            elif days_old <= 90:
                return 'moderate'
            elif days_old <= 365:
                return 'old'
            else:
                return 'very_old'
        except:
            return 'unknown'

    def _calculate_total_size(self, resources: List[Dict]) -> int:
        """Calculate total size of resources in bytes"""
        total_size = 0
        for resource in resources:
            size = resource.get('size')
            if size and isinstance(size, (int, str)):
                try:
                    total_size += int(size)
                except:
                    pass
        return total_size

    async def _analyze_resource(self, resource: Dict) -> Dict:
        """
        Analyze a resource for download feasibility

        Args:
            resource: Resource metadata

        Returns:
            Resource analysis
        """
        analysis = {
            'downloadable': True,
            'format': resource.get('format', 'unknown'),
            'size': resource.get('size'),
            'url': resource.get('url'),
            'last_modified': resource.get('last_modified'),
            'issues': []
        }

        # Check if URL is accessible
        url = resource.get('url')
        if not url:
            analysis['downloadable'] = False
            analysis['issues'].append('No download URL')
        elif not url.startswith(('http://', 'https://')):
            analysis['downloadable'] = False
            analysis['issues'].append('Invalid URL format')

        # Check size
        size = resource.get('size')
        if size:
            try:
                size_bytes = int(size)
                if size_bytes > 100 * 1024 * 1024:  # 100MB
                    analysis['issues'].append('Large file size (>100MB)')
                analysis['size_mb'] = round(size_bytes / (1024 * 1024), 2)
            except:
                analysis['issues'].append('Invalid size information')

        # Check format
        fmt = resource.get('format', '').upper()
        if fmt in ['CSV', 'JSON', 'XML']:
            analysis['machine_readable'] = True
        elif fmt in ['PDF', 'DOC', 'DOCX']:
            analysis['machine_readable'] = False
            analysis['issues'].append('Not machine-readable format')
        else:
            analysis['machine_readable'] = None
            analysis['issues'].append('Unknown format compatibility')

        return analysis

    async def test_connection(self) -> Dict:
        """
        Test connection to datos.gov.co API

        Returns:
            Connection test results
        """
        try:
            # Test with a simple API call
            result = await self.get_api_status()

            if result.get('status') == 'healthy':
                return {
                    'status': 'success',
                    'message': 'Successfully connected to datos.gov.co API',
                    'api_version': result.get('ckan_version'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'API responded but reported unhealthy status',
                    'details': result,
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to connect to datos.gov.co API: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }