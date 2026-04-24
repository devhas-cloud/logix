// ==========================================
// CONFIG.JS - Configuration Functions
// ==========================================

async function loadConfiguration() {
    try {
        const response = await fetch('/api/configuration');
        const config = await response.json();
        
        // General
        if (document.getElementById('config-timezone')) {
            document.getElementById('config-timezone').value = config.timezone || 'Asia/Jakarta';
        }
        if (document.getElementById('config-device-id')) {
            document.getElementById('config-device-id').value = config.device_id || '';
            
        }
        
        // Database
        if (document.getElementById('config-db-host')) {
            document.getElementById('config-db-host').value = config.db_host || '';
        }
        if (document.getElementById('config-db-port')) {
            document.getElementById('config-db-port').value = config.db_port || '';
        }
        if (document.getElementById('config-db-name')) {
            document.getElementById('config-db-name').value = config.db_name || '';
        }
        if (document.getElementById('config-db-user')) {
            document.getElementById('config-db-user').value = config.db_user || '';
        }
        if (document.getElementById('config-db-password')) {
            document.getElementById('config-db-password').value = config.db_password || '';
        }
        
        // KLHK
        if (document.getElementById('config-klhk-status')) {
            document.getElementById('config-klhk-status').value = config.klhk_status || 'inactive';
        }
        if (document.getElementById('config-klhk-api-url')) {
            document.getElementById('config-klhk-api-url').value = config.klhk_api_url || '';
        }
        if (document.getElementById('config-klhk-token-url')) {
            document.getElementById('config-klhk-token-url').value = config.klhk_token_url || '';
        }
        if (document.getElementById('config-klhk-uid')) {
            document.getElementById('config-klhk-uid').value = config.klhk_uid || '';
        }
        if (document.getElementById('config-klhk-fields')) {
            document.getElementById('config-klhk-fields').value = config.klhk_fields || '';
        }
        if (document.getElementById('config-klhk-max-dup-retry')) {
            document.getElementById('config-klhk-max-dup-retry').value = config.klhk_max_dup_retry || '';
        }
        if (document.getElementById('config-klhk-target-minute')) {
            document.getElementById('config-klhk-target-minute').value = config.klhk_target_minute || '';
        }
        
        // HAS
        if (document.getElementById('config-has-status')) {
            document.getElementById('config-has-status').value = config.has_status || 'inactive';
        }
        if (document.getElementById('config-has-api-url')) {
            document.getElementById('config-has-api-url').value = config.has_api_url || '';
        }
        if (document.getElementById('config-has-token-api')) {
            document.getElementById('config-has-token-api').value = config.has_token_api || '';
        }
        if (document.getElementById('config-has-fields')) {
            document.getElementById('config-has-fields').value = config.has_fields || '';
        }
        if (document.getElementById('config-has-logs-api-url')) {
            document.getElementById('config-has-logs-api-url').value = config.has_logs_api_url || '';
        }
        if (document.getElementById('config-has-logs-token-api')) {
            document.getElementById('config-has-logs-token-api').value = config.has_logs_token_api || '';
        }
        
        // Hidden fields from database
        if (document.getElementById('config-port-app')) {
            document.getElementById('config-port-app').value = config.port_number_app || '5010';
        }
        if (document.getElementById('config-port-log')) {
            document.getElementById('config-port-log').value = config.port_number_log || '3000';
        }
        if (document.getElementById('config-parameters')) {
            document.getElementById('config-parameters').value = config.parameters || '';
        }
        
        if (document.getElementById('config-gap-web')) {
            document.getElementById('config-gap-web').value = config.gap_web || '3';
        }
        if (document.getElementById('config-web-title')) {
            document.getElementById('config-web-title').value = config.web_title || '';
        }
        if (document.getElementById('config-web-name')) {
            document.getElementById('config-web-name').value = config.web_name || '';
        }
        if (document.getElementById('config-location-name')) {
            document.getElementById('config-location-name').value = config.location_name || '';
        }
        if (document.getElementById('config-software-version')) {
            document.getElementById('config-software-version').value = config.software_version || '';
        }
        if (document.getElementById('config-geo-latitude')) {
            document.getElementById('config-geo-latitude').value = config.geo_latitude || '0';
        }
        if (document.getElementById('config-geo-longitude')) {
            document.getElementById('config-geo-longitude').value = config.geo_longitude || '0';
        }
        if (document.getElementById('config-web-username')) {
            document.getElementById('config-web-username').value = config.web_username || 'admin';
        }
        if (document.getElementById('config-web-password')) {
            document.getElementById('config-web-password').value = config.web_password || 'has123456';
        }
        
        // Sensors
        const sensors = [
            'at500', 'rt200', 'sem5096', 'mace', 'iscan', 'ltnc', 'spectro',
            'contlyte', 'ds502', 'ammonia200', 'cod200x', 'h1601', 'ph200', 'tss200x', 'xymd02'
        ];
        
        sensors.forEach(sensor => {
            // Status
            if (document.getElementById(`config-${sensor}-status`)) {
                document.getElementById(`config-${sensor}-status`).value = config[`${sensor}_status`] || 'inactive';
            }
            // Port for most sensors
            if (document.getElementById(`config-${sensor}-port`)) {
                document.getElementById(`config-${sensor}-port`).value = config[`${sensor}_port`] || '';
            }
            // IP for SPECTRO
            if (document.getElementById(`config-${sensor}-ip`)) {
                document.getElementById(`config-${sensor}-ip`).value = config[`${sensor}_ip`] || '';
            }
            // Slave ID for XYMD02
            if (document.getElementById(`config-${sensor}-slave-id`)) {
                document.getElementById(`config-${sensor}-slave-id`).value = config[`${sensor}_slave_id`] || '';
            }
        });
        
        // Delay
        if (document.getElementById('config-delay')) {
            document.getElementById('config-delay').value = config.delay || '2';
        }
        
        showConfigAlert('✅ Konfigurasi berhasil dimuat', 'success');
    } catch (error) {
        console.error('Error loading configuration:', error);
        showConfigAlert('❌ Gagal memuat konfigurasi', 'danger');
    }
}

async function saveConfiguration() {
    Swal.fire({
        title: 'Konfirmasi Penyimpanan',
        text: 'Apakah Anda yakin ingin menyimpan konfigurasi ini?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#4f46e5',
        cancelButtonColor: '#9ca3af',
        confirmButtonText: 'Ya, Simpan',
        cancelButtonText: 'Batal'
    }).then(async (result) => {
        if (!result.isConfirmed) return;
        
        try {
            const configData = {
                // General
                timezone: document.getElementById('config-timezone')?.value || 'Asia/Jakarta',
                device_id: document.getElementById('config-device-id')?.value || '',
                
                // Database
                db_host: document.getElementById('config-db-host')?.value || '',
                db_port: document.getElementById('config-db-port')?.value || '',
                db_name: document.getElementById('config-db-name')?.value || '',
                db_user: document.getElementById('config-db-user')?.value || '',
                db_password: document.getElementById('config-db-password')?.value || '',
                
                // KLHK API
                klhk_status: document.getElementById('config-klhk-status')?.value || 'inactive',
                klhk_api_url: document.getElementById('config-klhk-api-url')?.value || '',
                klhk_token_url: document.getElementById('config-klhk-token-url')?.value || '',
                klhk_uid: document.getElementById('config-klhk-uid')?.value || '',
                klhk_fields: document.getElementById('config-klhk-fields')?.value || '',
                klhk_max_dup_retry: document.getElementById('config-klhk-max-dup-retry')?.value || '',
                klhk_target_minute: document.getElementById('config-klhk-target-minute')?.value || '',
                
                // HAS API
                has_status: document.getElementById('config-has-status')?.value || 'inactive',
                has_api_url: document.getElementById('config-has-api-url')?.value || '',
                has_token_api: document.getElementById('config-has-token-api')?.value || '',
                has_fields: document.getElementById('config-has-fields')?.value || '',
                has_logs_api_url: document.getElementById('config-has-logs-api-url')?.value || '',
                has_logs_token_api: document.getElementById('config-has-logs-token-api')?.value || '',
                
                // Additional fields from database
                port_number_app: document.getElementById('config-port-app')?.value || '5010',
                port_number_log: document.getElementById('config-port-log')?.value || '3000',
                parameters: document.getElementById('config-parameters')?.value || '',
                gap_web: document.getElementById('config-gap-web')?.value || '3',
                web_title: document.getElementById('config-web-title')?.value || '',
                web_name: document.getElementById('config-web-name')?.value || '',
                web_username: document.getElementById('config-web-username')?.value || 'admin',
                web_password: document.getElementById('config-web-password')?.value || 'has123456',
                location_name: document.getElementById('config-location-name')?.value || '',
                software_version: document.getElementById('config-software-version')?.value || '',
                geo_latitude: document.getElementById('config-geo-latitude')?.value || '0',
                geo_longitude: document.getElementById('config-geo-longitude')?.value || '0',
                
                // Sensors
                at500_status: document.getElementById('config-at500-status')?.value || 'inactive',
                at500_port: document.getElementById('config-at500-port')?.value || '',
                rt200_status: document.getElementById('config-rt200-status')?.value || 'inactive',
                rt200_port: document.getElementById('config-rt200-port')?.value || '',
                sem5096_status: document.getElementById('config-sem5096-status')?.value || 'inactive',
                sem5096_port: document.getElementById('config-sem5096-port')?.value || '',
                mace_status: document.getElementById('config-mace-status')?.value || 'inactive',
                mace_port: document.getElementById('config-mace-port')?.value || '',
                iscan_status: document.getElementById('config-iscan-status')?.value || 'inactive',
                iscan_port: document.getElementById('config-iscan-port')?.value || '',
                ltnc_status: document.getElementById('config-ltnc-status')?.value || 'inactive',
                ltnc_port: document.getElementById('config-ltnc-port')?.value || '',
                spectro_status: document.getElementById('config-spectro-status')?.value || 'inactive',
                spectro_ip: document.getElementById('config-spectro-ip')?.value || '',
                spectro_port: document.getElementById('config-spectro-port')?.value || '',
                contlyte_status: document.getElementById('config-contlyte-status')?.value || 'inactive',
                contlyte_port: document.getElementById('config-contlyte-port')?.value || '',
                ds502_status: document.getElementById('config-ds502-status')?.value || 'inactive',
                ds502_port: document.getElementById('config-ds502-port')?.value || '',
                ammonia200_status: document.getElementById('config-ammonia200-status')?.value || 'inactive',
                ammonia200_port: document.getElementById('config-ammonia200-port')?.value || '',
                cod200x_status: document.getElementById('config-cod200x-status')?.value || 'inactive',
                cod200x_port: document.getElementById('config-cod200x-port')?.value || '',
                h1601_status: document.getElementById('config-h1601-status')?.value || 'inactive',
                h1601_port: document.getElementById('config-h1601-port')?.value || '',
                ph200_status: document.getElementById('config-ph200-status')?.value || 'inactive',
                ph200_port: document.getElementById('config-ph200-port')?.value || '',
                tss200x_status: document.getElementById('config-tss200x-status')?.value || 'inactive',
                tss200x_port: document.getElementById('config-tss200x-port')?.value || '',
                xymd02_status: document.getElementById('config-xymd02-status')?.value || 'inactive',
                xymd02_port: document.getElementById('config-xymd02-port')?.value || '',
                xymd02_slave_id: document.getElementById('config-xymd02-slave-id')?.value || '',
                delay: document.getElementById('config-delay')?.value || '2',

                

                
            };
            
            console.log('Sending config data:', configData);
            
            const response = await fetch('/api/configuration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData)
            });
                
                const result = await response.json();
                console.log('Response:', result);
                
                if (result.success) {
                    showConfigAlert('✅ Konfigurasi berhasil disimpan', 'success');
                    setTimeout(() => {
                        loadConfiguration();
                    }, 500);
                } else {
                    showConfigAlert('❌ Error: ' + (result.error || 'Unknown error'), 'danger');
                }
        } catch (error) {
            console.error('Error saving configuration:', error);
            showConfigAlert('❌ Error: ' + error.message, 'danger');
        }
    });
}
