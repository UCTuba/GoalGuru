from task_tracker import create_app, db
from task_tracker.models import Task, User
from flask import render_template, request, redirect, url_for, jsonify
from datetime import datetime

app = create_app()

@app.route('/')
def index():
    # Check for sorting query parameter
    sort = request.args.get('sort')
    search_query = request.args.get('search', '')

    # Filter tasks based on the search query
    tasks = Task.query.filter(
        Task.title.ilike(f'%{search_query}%'),
        Task.completed == False
    )
    if sort == 'assignment_date':
        tasks = Task.query.filter_by(completed=False).order_by(Task.assignment_date).all()
    elif sort == 'target_date':
        tasks = Task.query.filter_by(completed=False).order_by(Task.target_date).all()
    else:
        tasks = Task.query.filter_by(completed=False).all()  # Only show incomplete tasks

    # Convert tasks to a serializable format
    tasks_list = [task.to_dict() for task in tasks]

    return render_template('index.html', tasks=tasks_list, search_query=search_query)


from datetime import datetime

@app.route('/completed_tasks')
def completed_tasks():
    search_query = request.args.get('search', '')

    # Filter completed tasks based on the search query and order them by department and completed_date
    completed_tasks_list = Task.query.filter(
        Task.completed == True,
        Task.title.ilike(f'%{search_query}%')
    ).order_by(Task.department, Task.completed_date.desc()).all()

    # Convert `completed_date` and `target_date` to datetime objects
    for task in completed_tasks_list:
        if isinstance(task.completed_date, str):
            task.completed_date = datetime.strptime(task.completed_date, '%Y-%m-%d')
        if isinstance(task.target_date, str):
            task.target_date = datetime.strptime(task.target_date, '%Y-%m-%d')

    # Group tasks by department
    tasks_by_department = {}
    for task in completed_tasks_list:
        tasks_by_department.setdefault(task.department, []).append(task)

    return render_template('completed_tasks.html', tasks_by_department=tasks_by_department, search_query=search_query)

@app.route('/count_tasks', methods=['GET'])
def count_tasks():
    open_task_count = Task.query.filter_by(completed=False).count()
    return jsonify({"open_task_count": open_task_count}), 200

@app.route('/delete', methods=['POST'])
def delete_tasks():
    try:
        task_ids = request.json.get('tasks', [])
        
        # Check if tasks exist and delete them
        Task.query.filter(Task.id.in_(task_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting tasks: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        department = request.form['department']
        assigned_user_id = request.form.get('assigned_user')
        assignment_date = request.form.get('assignment_date')
        target_date = request.form.get('target_date')
        
        assignment_date_obj = datetime.strptime(assignment_date, '%Y-%m-%d').date() if assignment_date else None
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date() if target_date else None

        new_task = Task(
            title=title,
            description=description,
            department=department,
            assigned_user_id=int(assigned_user_id) if assigned_user_id else None,
            assignment_date=assignment_date_obj,
            target_date=target_date_obj
        )
        db.session.add(new_task)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('create.html', users=users)

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    if request.is_json:
        data = request.get_json()
        completed = data.get("completed", False)
        
        task = Task.query.get(task_id)
        if task:
            task.completed = completed
            if completed:
                task.completed_date = datetime.now().date()
            else:
                task.completed_date = None
            db.session.commit()

            # Get updated open task count
            open_task_count = Task.query.filter_by(completed=False).count()
            return jsonify({"success": True, "open_task_count": open_task_count}), 200
    return jsonify({"success": False}), 400

@app.route('/revert/<int:task_id>', methods=['POST'])
def revert_task(task_id):
    task = Task.query.get(task_id)
    if task and task.completed:
        task.completed = False
        task.completed_date = None  # Remove completion date
        db.session.commit()
    return redirect(url_for('completed_tasks'))

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def view_task(task_id):
    task = Task.query.get(task_id)
    if request.method == 'POST':
        # Update description
        if 'description' in request.form:
            task.description = request.form['description']
        
        # Update due date
        if 'target_date' in request.form:
            new_target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d').date()
            
            # Save current target date to history if changing
            if task.target_date and task.target_date != new_target_date:
                if task.due_date_history is None:
                    task.due_date_history = []
                task.due_date_history.append(task.target_date)
                task.edit_count += 1
            task.target_date = new_target_date
        
        db.session.commit()
        return redirect(url_for('view_task', task_id=task_id))
    
    return render_template('view_task.html', task=task)

if __name__ == '__main__':
    app.run(debug=True)
