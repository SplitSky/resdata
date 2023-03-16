% File should be loaded as "rings"

% Project name not yet used...
project = "nanorings";
% Get column names
col_names = fieldnames(rings);
% Open file
fn=fopen('json_version.json','a+');

% Loop over columns
for i =1:numel(col_names)-3
    % Get the column from the table
    column = rings(:,col_names{i});
    % Convert the data in a cell array
    try
        % Start conversion
        fprintf('Starting conversion of %s...', col_names{i});
        % Run encode
        data_json = jsonencode(table2cell(column));
    catch
        % Catch errors
        fprintf('%s does not work\n',col_names{i});
        % Skip
        continue;
    end
        % Make into key-value
    col_json = sprintf('{"%s":%s}',col_names{i},data_json);
    % Write to file
    fwrite(fn,col_json);
    % State complete
    fprintf('Done %s\n',col_names{i});
end

%% Close file
fclose(fn);