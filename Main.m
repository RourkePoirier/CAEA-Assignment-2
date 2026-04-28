%
% ENME802 - CAEA Assignment 1
%
%%% Group Members: %%%
% Matthew Smith 22173112
% Rourke Poirer
% Steve Millar
% Jackson Long
%
%%% Authorship: %%%
% Modified from code provided by Sarat Singamneni in CAEA Lectures
% Variable names are honoured but code has been restructured for clarity
% 
%%% Functionality: %%%
% Takes data_structure.xlsx file as input and executes
% 2D Finite Element Analysis to solve for displacement, stress_x, stress_y,
% and stress_xy

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SETUP ROUTINE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Read External Data File
array = readmatrix('data_structure.xlsx');
data = array;

% Assign variables from file (HARDCODED data positions)
n_element =     data(1,1);
n_nodes =       data(1,2);
E =             data(1,8);
A =             data(1,9);
ncon =          [data(:,3),data(:,4),data(:,5)];
X =             data(:,6);
Y =             data(:,7);
NDU =           data(1,11);
dzero =         data(:,12);
F =             data(:,10);
v =             data(1,13);
t =             data(1,14);

% Initialise Matrices
KE = zeros(6);
K = zeros(2*n_nodes);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% MAIN ROUTINE
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Iterate through all triangular elements
for i = 1:n_element
    
    % Construct Nodes from data
    nodes = ncon(i,:);
    coords = [X(nodes), Y(nodes)];

    % Calculate Elemental Stiffness Matrix for this element
    [KE] = calculate_elemental_stiffness_matrix(coords, E, v, t);
    
    % Assemble Nodes of element
    n1 = ncon(i,1);
    n2 = ncon(i,2);
    n3 = ncon(i,3);

    % Assign 6DOF of nodes
    ROC(1) = (2*n1)-1;
    ROC(2) = (2*n1);
    ROC(3) = (2*n2)-1;
    ROC(4) = (2*n2);
    ROC(5) = (2*n3)-1;
    ROC(6) = (2*n3);
    
    % 2D Iteration to construct overall Stiffness Matrix, K 
    % FEA Assembly Process
    for IX = 1:6
        MI = ROC(IX);

        for JX = 1:6
            MJ = ROC(JX);
            K(MI, MJ) = K(MI, MJ) + KE(IX, JX);
        end
    end
end

% Apply Boundary conditions
KM = apply_boundary_conditions(K, dzero, NDU);

% Solve Global Displacements, U
U = KM \ F;

% Solve Global stresses
[Sx, Sy, Sxy] = calculate_element_stresses(n_element, ncon, X, Y, U, E, v);

% Write outputs to Excel files
writematrix(U,   'displacement.xlsx')
writematrix(Sx,  'stress_x.xlsx'    )
writematrix(Sy,  'stress_y.xlsx'    )
writematrix(Sxy, 'stress_xy.xlsx'   )

% Call Display function
% display_structure(n_element, ncon, X, Y, U);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% FUNCTION DEFINITIONS 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Calculate one elemental stiffness matrix (Called for every element)
function [KE] = calculate_elemental_stiffness_matrix(coords, E, v, t)

    % Get Area of element + Strain-Displacement and Strain-Stress Matrices
    A = calc_triangle_area(coords);
    B = calc_strain_displacement_matrix(coords, A);
    D = calc_strain_stress_matrix(E, v);

    % Calculate and Return KE (Elemental Stiffness Matrix):
    % t = element thickness
    % A = Area of Element
    % B = Strain-Displacement Matrix
    % D = Strain-Stress Matrix
    KE = t * A * (B.') * D * B;

end

% Applies bound cond. given
% dzero is an array of indicies describing fixed degrees of freedom (DOF)
% NDU is the number of boundary indicies (i.e. length(dzero))
function [KM] = apply_boundary_conditions(K, dzero, NDU)
    KM = K;

    % For each boundary condition apply
    for k = 1:NDU
        n = dzero(k);
        KM(n,:) = 0; % Zero the row
        KM(:,n) = 0; % Zero the column
        KM(n,n) = 1; % Set diagonal
    end

end

% Calculate stresses for all elements
function [Sx, Sy, Sxy] = calculate_element_stresses(n_element, ncon, X, Y, U, E, v)
    for i = 1:n_element
        nodes = ncon(i,:);
        coords = [X(nodes), Y(nodes)];

        A = calc_triangle_area(coords);
        B = calc_strain_displacement_matrix(coords, A);
        D = calc_strain_stress_matrix(E, v);

        % Local displacements
        Ue = [U(2*nodes(1)-1); U(2*nodes(1));
              U(2*nodes(2)-1); U(2*nodes(2));
              U(2*nodes(3)-1); U(2*nodes(3))];

        sigma = D * B * Ue;
        Sx(i) = sigma(1);
        Sy(i) = sigma(2);
        Sxy(i) = sigma(3);
    end
end

%%%%% HELPER CALCULATION FUNCTIONS %%%%%
% Use X and Y array of triangular element to find Area
function [A] = calc_triangle_area(coords)

    % Construct X and Y arrays from coords
    x = coords(:,1);
    y = coords(:,2);

    % Calculate Area of Triangular Element
    A = 0.5 * det( ...
        [ ...
          1 x(1) y(1)  ; ...
          1 x(2) y(2)  ; ...
          1 x(3) y(3)    ...
        ]);

end

function [B] = calc_strain_displacement_matrix(coords, A)

    % Assign individual variables from coords array
    x1 = coords(1,1); y1 = coords(1,2);
    x2 = coords(2,1); y2 = coords(2,2);
    x3 = coords(3,1); y3 = coords(3,2);

    % Coefficients
    b1 = (y2-y3);
    b2 = (y3-y1);
    b3 = (y1-y2);
    c1 = (x3-x2);
    c2 = (x1-x3);
    c3 = (x2-x1);

    % Construct and return B Matrix
    B = (1/(2*A)) * ...
        [
            b1 0 b2 0 b3 0;
            0 c1 0 c2 0 c3;
            c1 b1 c2 b2 c3 b3;
        ];

end

% E = Young's Modulus (Of the material)
% v = Poisson's Ratio (lateral deformation coupling)
function [D] = calc_strain_stress_matrix(E, v)

    % Construct D Matrix
    D = (E/(1-v^2))*[
    
        1 v 0
        v 1 0
        0 0 (1-v)/2
    
    ];

end

