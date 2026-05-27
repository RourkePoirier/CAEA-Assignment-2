clear; clc;

%% Read existing Project 1 mesh data
inputFile = 'data_structure.xlsx';
outputFile = 'project2_results.xlsx';

if ~isfile(inputFile)
    error('Cannot find %s in the current MATLAB folder.', inputFile);
end

data = readmatrix(inputFile, 'Sheet', 'Sheet1');

n_element = data(1,1);
n_nodes = data(1,2);
ncon = data(1:n_element, 3:5);

% Project 1 geometry is in mm. Keep original values for output but convert
% to m for thermal FEA calculations.
X_original = data(1:n_nodes, 6);
Y_original = data(1:n_nodes, 7);
t_project = data(1,14);

geometry_units = getOptionalTextParam(inputFile, 'thermal_properties', 'geometry_units', 'mm');
if strcmpi(geometry_units, 'm')
    X = X_original;
    Y = Y_original;
else
    X = X_original / 1000;
    Y = Y_original / 1000;
end

%% 2. Read cutting data from spreadsheet - Needs a cutting data spreadsheet
Vc_m_min = getRequiredParam(inputFile, 'cutting_data', 'Vc_m_min');
depth_cut_mm = getRequiredParam(inputFile, 'cutting_data', 'depth_cut_mm');
feed_mm_rev = getRequiredParam(inputFile, 'cutting_data', 'feed_mm_rev');
rake_angle_deg = getRequiredParam(inputFile, 'cutting_data', 'rake_angle_deg');
a2_mm = getRequiredParam(inputFile, 'cutting_data', 'a2_mm');
L_contact_mm = getRequiredParam(inputFile, 'cutting_data', 'L_contact_mm');
Pz_N = getRequiredParam(inputFile, 'cutting_data', 'Pz_N');
Pxy_N = getRequiredParam(inputFile, 'cutting_data', 'Pxy_N');

heat_fraction_tool = getOptionalParam(inputFile, 'cutting_data','heat_fraction_tool', 0.3);
flank_heat_fraction = getOptionalParam(inputFile, 'cutting_data','flank_heat_fraction', 0.2);

%% 3. Read thermal material properties
kx = getOptionalParam(inputFile,'thermal_properties','kx_W_mK', 85);
ky = getOptionalParam(inputFile,'thermal_properties','ky_W_mK', 85);

if sheetHasParam(inputFile, 'thermal_properties', 'thickness_m')
    t = getRequiredParam(inputFile, 'thermal_properties', 'thickness_m');
elseif sheetHasParam(inputFile, 'thermal_properties', 'thickness_mm')
    t = getRequiredParam(inputFile, 'thermal_properties', 'thickness_mm') /1000;
else
    if t_project > 0.1
        t = t_project / 1000;
    else
        t = t_project;
    end
end

T_fixed_default = getOptionalParam(inputFile, 'thermal_properties', 'T_fixed_C', 20);
T_infinity_default = getOptionalParam(inputFile, 'thermal_properties', 'T_infinity_C', 20);

%% 4. Cutting heat calculation based on frictional work
% unit conversions
Vc_m_s = Vc_m_min / 60;
depth_m = depth_cut_mm / 1000;
feed_m = feed_mm_rev / 1000;
a2_m = a2_mm / 1000;
L_contact_m = L_contact_mm / 1000;
alpha = deg2rad(rake_angle_deg);

%chip ratio and shear angle
chip_ratio = feed_m / a2_m;
phi = atan((chip_ratio * cos(alpha)) / (1 - chip_ratio * sin(alpha)));
phi_deg = rad2deg(phi);

% Merchant Circle, pz = main cutting force, pxy = feed force
friction_force_N = Pz_N * sin(alpha) + Pxy_N * cos(alpha);
normal_force_N = Pz_N * cos(alpha) - Pxy_N * sin(alpha);
friction_angle_deg = rad2deg(atan(friction_force_N / normal_force_N));

%chip velocity along rake face
chip_velocity_m_s = Vc_m_s * chip_ratio;

%heat generated at chip tool interface from frictional work.
friction_power_W = friction_force_N * chip_velocity_m_s;
heat_into_tool_W = heat_fraction_tool * friction_power_W;

%heat flux over chip tool contact area
contact_area_m2 = L_contact_m * depth_m;
calculated_rake_heat_flux = heat_into_tool_W / contact_area_m2;

% Optional flank/bevel heat flux, used only if thermal_bc uses AutoFlank.
calculated_flank_heat_flux = flank_heat_fraction * calculated_rake_heat_flux;

% Total cutting power, kept only as a reference value in the summary output.
cutting_power_W = Pz_N * Vc_m_s;

%% 5. Assemble global thermal conduction matrix
K = zeros(n_nodes, n_nodes);
F = zeros(n_nodes, 1);
D = [kx 0; 0 ky];

for e = 1:n_element
    nodes = ncon(e,:);
    coords = [X(nodes), Y(nodes)];

    [Aele, B] = thermalTriangleB(coords);
    KE = t * Aele * (B.') * D * B;

    for i = 1:3
        row = nodes(i);
        for j = 1:3
            col = nodes(j);
            K(row,col) = K(row, col) + KE(i,j);
        end
    end
end

%% 6. Apply thermal boundary conditions
if ~sheetExists(inputFile, 'thermal_bc')
    error(['Missing thermal_bc'])
end

bc = readcell(inputFile, 'Sheet','thermal_bc');
fixedTempCount = 0;
convectionCount = 0;

for r = 2:size(bc,1) % starts after header row
    if size(bc,2) < 2 || ismissingCell(bc{r,1})
        continue;
    end

    type = lower(strtrim(string(bc{r,1})));
    n1 = readCellNumber(bc{r,2});

    if contains(type, 'fixed')
        Tvalue = T_fixed_default;
        if size(bc, 2) >= 4 && ~ismissingCell(bc{r,4})
            Tvalue = readCellNumber(bc{r, 4});
        end
        % Apply fixed temperature to node 1
        [K, F] = applyFixedTemperature(K, F, n1, Tvalue);
        fixedTempCount = fixedTempCount + 1;
        % Apply fixed temperature to node 2 as well (both endpoints of edge must be constrained)
        if size(bc,2) >= 3 && ~ismissingCell(bc{r,3})
            n2 = readCellNumber(bc{r,3});
            [K, F] = applyFixedTemperature(K, F, n2, Tvalue);
        end

    elseif contains(type, 'heat') || contains(type, 'flux')
        n2 = readCellNumber(bc{r,3});
        q = calculated_rake_heat_flux;

        if size(bc,2) >= 4 && ~ismissingCell(bc{r,4})
            valueText = string(bc{r,4});
            if strcmpi(valueText, 'Auto') || strcmpi(valueText, 'AutoRake')
                q = calculated_rake_heat_flux;
            elseif strcmpi(valueText, 'AutoFlank')
                q = calculated_flank_heat_flux;
            else 
                q = readCellNumber(bc{r,4});
            end
        end

        edgeLength = sqrt((X(n2) - X(n1))^2 + (Y(n2) - Y(n1))^2);
        F(n1) = F(n1) + q * t * edgeLength/2;
        F(n2) = F(n2) + q * t * edgeLength/2;

    elseif contains(type, 'conv')
        n2 = readCellNumber(bc{r,3});

        % Column 4 must contain the convection coefficient h
        if size(bc,2) < 4 || ismissingCell(bc{r,4})
            warning('Convection BC on row %d is missing h value in column 4 — row skipped.', r);
            continue;
        end
        h = readCellNumber(bc{r,4});

        Tinf = T_infinity_default;
        if size(bc,2) >= 5 && ~ismissingCell(bc{r,5})
            Tinf = readCellNumber(bc{r,5});
        end

        edgeLength = sqrt((X(n2) - X(n1))^2 + (Y(n2) - Y(n1))^2);
        Kedge = h * t * edgeLength / 6 * [2 1; 1 2];
        Fedge = h * Tinf * t * edgeLength/2 * [1;1];

        edgeNodes = [n1 n2];
        for i = 1:2
            F(edgeNodes(i)) = F(edgeNodes(i)) + Fedge(i);
            for j = 1:2
                K(edgeNodes(i), edgeNodes(j)) = K(edgeNodes(i), edgeNodes(j)) + Kedge(i,j);
            end
        end
        convectionCount = convectionCount + 1;

    elseif contains(type, 'insulated')
        % No action. Zero heat flux is the default boundary condition.

    else
        warning('Unknown thermal BC type on row %d: %s. This row was ignored.', r, type);
    end
end

if fixedTempCount == 0 && convectionCount == 0
    warning(['No fixed temp or convection boundary conditions found'])
end

%% 7. Solve nodal temperatures
temperature = K \ F;

%% 8. Calculate conductive heat flux in each element
qx = zeros(n_element,1);
qy = zeros(n_element,1);
qmag = zeros(n_element,1);

for e = 1:n_element
    nodes = ncon(e,:);
    coords = [X(nodes), Y(nodes)];
    [~, B] = thermalTriangleB(coords);

    Te = temperature(nodes);
    q = -D * B * Te;

    qx(e) = q(1);
    qy(e) = q(2);
    qmag(e) = sqrt(qx(e)^2 + qy(e)^2);
end

%% 9. Write results for plotting/GUI use
temperature_results = table((1:n_nodes).', X_original, Y_original, X, Y, temperature, 'VariableNames', ...
    {'Node', 'X_original', 'Y_original', 'X_m', 'Y_m', 'Temperature_C'});

thermal_flux_results = table((1:n_element).', ncon(:,1), ncon(:,2), ncon(:,3), qx, qy, qmag, ...
    'VariableNames',{'Element', 'Node1', 'Node2', 'Node3', 'qx_W_m2','qy_W_m2', 'qmag_W_m2'});

cutting_summary = table( ...
    Vc_m_min, depth_cut_mm, feed_mm_rev, rake_angle_deg, a2_mm, L_contact_mm, ...
    Pz_N, Pxy_N, chip_ratio, phi_deg, friction_force_N, normal_force_N, ...
    friction_angle_deg, chip_velocity_m_s, friction_power_W, heat_fraction_tool, ...
    heat_into_tool_W, calculated_rake_heat_flux, flank_heat_fraction, calculated_flank_heat_flux, ...
    cutting_power_W, kx, ky, t, T_fixed_default, T_infinity_default, ...
    'VariableNames', {'Vc_m_min','depth_cut_mm','feed_mm_rev','rake_angle_deg', ...
    'a2_mm','L_contact_mm','Pz_N','Pxy_N','chip_ratio','shear_angle_deg', ...
    'friction_force_N','normal_force_N','friction_angle_deg','chip_velocity_m_s', ...
    'friction_power_W','heat_fraction_tool','heat_into_tool_W','rake_heat_flux_W_m2', ...
    'flank_heat_fraction','flank_heat_flux_W_m2','cutting_power_W_for_reference', ...
    'kx_W_mK','ky_W_mK','thickness_m','T_fixed_default_C','T_infinity_default_C'});

writetable(temperature_results, outputFile, 'Sheet', 'temperature_results');
writetable(thermal_flux_results, outputFile, 'Sheet', 'thermal_flux_results');
writetable(cutting_summary, outputFile, 'Sheet', 'cutting_summary');

fprintf('Project 2 thermal analysis complete. Results written to %s\n', outputFile);

%% Local Functions

function value  = getRequiredParam(file, sheet, name)
    if ~sheetExists(file, sheet)
        error('Missing required sheet: %s', sheet);
    end
    
    raw = readcell(file, 'Sheet', sheet);
    value = [];
    
    for i = 1:size(raw,1)
        if ~ismissingCell(raw{i,1}) && strcmpi(strtrim(string(raw{i,1})),name)
            value = readCellNumber(raw{i,2});
            return;
        end
    end
    
    error('Missing required variable %s in sheet %s.', name, sheet)
end

function value = getOptionalParam(file, sheet, name, defaultValue)
    value = defaultValue;
    if ~sheetExists(file, sheet)
        return;
    end

    raw = readcell(file, 'Sheet', sheet);
    for i = 1:size(raw,1)
        if ~ismissingCell(raw{i,1}) && strcmpi(strtrim(string(raw{i,1})), name)
            value = readCellNumber(raw{i,2});
            return;
        end
    end
end

function value = getOptionalTextParam(file, sheet, name, defaultValue)
    value = defaultValue;
    if ~sheetExists(file, sheet)
        return;
    end

    raw = readcell(file, 'Sheet', sheet);
    for i = 1:size(raw,1)
        if ~ismissingCell(raw{i,1}) && strcmpi(strtrim(string(raw{i,1})), name)
            value = string(raw{i,2});
            return;
        end
    end
end

function tf = sheetHasParam(file, sheet, name)
    tf = false;
    if ~sheetExists(file, sheet)
        return;
    end

    raw = readcell(file, 'Sheet', sheet);
    for i = 1:size(raw,1)
        if ~ismissingCell(raw{i,1}) && strcmpi(strtrim(string(raw{i,1})), name)
            tf = true;
            return;
        end
    end
end

function tf = sheetExists(file, sheetName)
    sheets = sheetnames(file);
    tf = any(strcmpi(sheets, sheetName));
end

function [A, B] = thermalTriangleB(coords)
    x1 = coords(1,1); y1 = coords(1,2);
    x2 = coords(2,1); y2 = coords(2,2);
    x3 = coords(3,1); y3 = coords(3,2);

    A = 0.5 * det([1 x1 y1; 1 x2 y2; 1 x3 y3]);

    if abs(A) < eps
        error('A triangular element has zero or near-zero area. Check the mesh.');
    end

    A = abs(A);

    b1 = y2 - y3;
    b2 = y3 - y1;
    b3 = y1 - y2;

    c1 = x3 - x2;
    c2 = x1 - x3;
    c3 = x2 - x1;

    B = (1/(2*A)) * [b1 b2 b3; c1 c2 c3];
end

function [Kmod, Fmod] = applyFixedTemperature(K, F, node, temperature)
    % Correct elimination method for a non-zero prescribed temperature.
    % First move the known-temperature contribution to the right-hand side,
    % then zero the row/column and set the diagonal to one.
    Kmod = K;
    Fmod = F;

    Fmod = Fmod - Kmod(:,node) * temperature;

    Kmod(node,:) = 0;
    Kmod(:,node) = 0;
    Kmod(node,node) = 1;
    Fmod(node) = temperature;
end

function value = readCellNumber(cellValue)
    if isnumeric(cellValue)
        value = cellValue;
    elseif ischar(cellValue) || isstring(cellValue)
        value = str2double(cellValue);
    else
        value = NaN;
    end

    if isnan(value)
        error('A numeric spreadsheet value could not be read. Check the input sheets.');
    end
end

function tf = ismissingCell(cellValue)
    tf = isempty(cellValue) || ...
         (isnumeric(cellValue) && isnan(cellValue)) || ...
         (isstring(cellValue) && strlength(cellValue) == 0) || ...
         (ischar(cellValue) && isempty(strtrim(cellValue)));
end