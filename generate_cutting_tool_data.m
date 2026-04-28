function out = generate_cutting_tool_data()

% Units:
% Geometry : mm
% E        : MPa (N/mm^2)
% Force    : N
% Thickness: mm

    project_folder = fileparts(mfilename('fullpath'));

    % Mesh
    p.mesh_size_mm = 0.6;

    % Material
    p.E_MPa = 210000;
    p.v = 0.30;
    p.thickness_mm = 1.0;

    % Loads
    p.cutting_force_N = 1000;
    p.thrust_force_N = -500;
    p.load_radius_mm = 0.75;

    % Clamp
    p.clamp_length_mm = 1.5;

    %% Build default cutting tool geometry
    polygon_xy = build_tool_polygon();

    %% Generate interior points for meshing
    interior_points = generate_interior_points(polygon_xy, p.mesh_size_mm);
    all_points = [polygon_xy; interior_points];
    all_points = unique(round(all_points, 9), 'rows', 'stable');

    %% Triangulate and keep only elements inside tool
    DT = delaunayTriangulation(all_points);
    tri = DT.ConnectivityList;
    pts = DT.Points;

    centroids = (pts(tri(:,1),:) + pts(tri(:,2),:) + pts(tri(:,3),:)) / 3;
    in = inpolygon(centroids(:,1), centroids(:,2), polygon_xy(:,1), polygon_xy(:,2));
    tri = tri(in, :);

    % Ensure all triangles are oriented consistently
    for i = 1:size(tri,1)
        coords = pts(tri(i,:), :);
        if signed_triangle_area(coords) < 0
            tri(i,[2 3]) = tri(i,[3 2]);
        end
    end

    %% Basic FEA arrays
    n_element = size(tri, 1);
    n_nodes = size(pts, 1);

    ncon = tri;
    X = pts(:,1);
    Y = pts(:,2);

    E = p.E_MPa;
    v = p.v;
    t = p.thickness_mm;
    A = polyarea(polygon_xy(:,1), polygon_xy(:,2));

    %% Boundary conditions (right end clamped)
    xmax = max(X);
    fixed_node_ids = find(X >= (xmax - p.clamp_length_mm));

    dzero = zeros(2*numel(fixed_node_ids), 1);
    idx = 1;
    for k = 1:numel(fixed_node_ids)
        node_id = fixed_node_ids(k);
        dzero(idx)   = 2*node_id - 1; % x DOF
        dzero(idx+1) = 2*node_id;     % y DOF
        idx = idx + 2;
    end
    NDU = length(dzero);

    %% Load vector - apply near tool tip
    F = zeros(2*n_nodes, 1);

    % Tool tip target location
    tip_target = [0, 0];
    distances = hypot(X - tip_target(1), Y - tip_target(2));
    load_node_ids = find(distances <= p.load_radius_mm);

    % Fallback in case no node lies inside the chosen radius
    if isempty(load_node_ids)
        [~, nearest_id] = min(distances);
        load_node_ids = nearest_id;
    end

    fx_each = p.cutting_force_N / numel(load_node_ids);
    fy_each = p.thrust_force_N / numel(load_node_ids);

    for k = 1:numel(load_node_ids)
        node_id = load_node_ids(k);
        F(2*node_id - 1) = F(2*node_id - 1) + fx_each;
        F(2*node_id)     = F(2*node_id)     + fy_each;
    end

    %% Export to Excel (match Python/default format exactly)
    headers = {'n_element','n_nodes','ncon1','ncon2','ncon3', ...
               'X','Y','E','A','F','NDU','dzero','v','t'};

    n_rows = max([n_element, n_nodes, numel(F), NDU, 1]);
    data = cell(n_rows + 1, 14);   % +1 because row 1 is the header row

    % Header row
    data(1,:) = headers;

    % First data row carries the single-value metadata
    data{2,1}  = n_element;
    data{2,2}  = n_nodes;
    data{2,8}  = E;
    data{2,9}  = A;
    data{2,11} = NDU;
    data{2,13} = v;
    data{2,14} = t;

    % Element connectivity
    for i = 1:n_element
        data{i+1,3} = ncon(i,1);
        data{i+1,4} = ncon(i,2);
        data{i+1,5} = ncon(i,3);
    end

    % Node coordinates
    for i = 1:n_nodes
        data{i+1,6} = X(i);
        data{i+1,7} = Y(i);
    end

    % Global force vector
    for i = 1:numel(F)
        data{i+1,10} = F(i);
    end

    % Constrained DOF list
    for i = 1:NDU
        data{i+1,12} = dzero(i);
    end

    excel_path = fullfile(project_folder, 'data_structure.xlsx');
    writecell(data, excel_path, "WriteMode","replacefile");

    %% Save preview plot
    fig = figure('Visible', 'off');
    triplot(ncon, X, Y, 'g');
    hold on;

    plot([polygon_xy(:,1); polygon_xy(1,1)], ...
         [polygon_xy(:,2); polygon_xy(1,2)], ...
         'r-', 'LineWidth', 1.8);

    if ~isempty(fixed_node_ids)
        plot(X(fixed_node_ids), Y(fixed_node_ids), ...
             'bs', 'MarkerFaceColor', 'b');
    end

    if ~isempty(load_node_ids)
        plot(X(load_node_ids), Y(load_node_ids), ...
             'ro', 'MarkerFaceColor', 'r');
    end

    axis equal;
    grid on;
    xlabel('X (mm)');
    ylabel('Y (mm)');
    title('Default Cutting Tool Mesh, Clamp Nodes, and Load Nodes');


    legend('Mesh', 'Tool boundary', 'Clamped nodes', 'Loaded nodes', ...
           'Location', 'best');

    hold off;

    preview_path = fullfile(project_folder, 'default_cutting_tool_preview.png');
    exportgraphics(fig, preview_path, 'Resolution', 300);
    close(fig);

    %% Return output structure
    out = struct();
    out.project_folder = project_folder;
    out.excel_path = excel_path;
    out.preview_path = preview_path;
    out.n_element = n_element;
    out.n_nodes = n_nodes;
    out.fixed_node_ids = fixed_node_ids;
    out.load_node_ids = load_node_ids;
    out.polygon_xy = polygon_xy;
    out.X = X;
    out.Y = Y;
    out.ncon = ncon;
    out.F = F;
    out.dzero = dzero;
    out.NDU = NDU;

    fprintf('Default cutting tool data generated successfully.\n');
    fprintf('Excel file:   %s\n', excel_path);
    fprintf('Preview plot: %s\n', preview_path);
    fprintf('Nodes: %d | Elements: %d\n', n_nodes, n_element);
end

%% Local functions

function polygon_xy = build_tool_polygon()
    % Fixed default cutting tool profile
    polygon_xy = [
        0.00   0.0;
        0.50   0.0;
        6.00   0.0;
        12.00  0.0;
        11.20 -4.0;
        6.00  -4.0;
        0.78  -4.0
    ];
end

function interior_points = generate_interior_points(polygon_xy, h)
    xmin = min(polygon_xy(:,1));
    xmax = max(polygon_xy(:,1));
    ymin = min(polygon_xy(:,2));
    ymax = max(polygon_xy(:,2));

    xg = xmin:h:xmax;
    yg = ymin:h:ymax;

    [XX, YY] = meshgrid(xg, yg);
    candidate_points = [XX(:), YY(:)];

    [in, on] = inpolygon(candidate_points(:,1), candidate_points(:,2), ...
                         polygon_xy(:,1), polygon_xy(:,2));

    interior_points = candidate_points(in | on, :);

    % Remove points too close to the existing polygon vertices
    keep = true(size(interior_points,1),1);
    for i = 1:size(interior_points,1)
        d = hypot(interior_points(i,1) - polygon_xy(:,1), ...
                  interior_points(i,2) - polygon_xy(:,2));
        if any(d < 0.15*h)
            keep(i) = false;
        end
    end
    interior_points = interior_points(keep, :);
end

function A = signed_triangle_area(coords)
    x1 = coords(1,1); y1 = coords(1,2);
    x2 = coords(2,1); y2 = coords(2,2);
    x3 = coords(3,1); y3 = coords(3,2);

    A = 0.5 * det([1 x1 y1; 1 x2 y2; 1 x3 y3]);
end